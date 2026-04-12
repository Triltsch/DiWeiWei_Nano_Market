import { useCallback, useEffect, useId, useRef, useState } from "react";

import {
  createChatSession,
  getChatMessages,
  listChatSessions,
  sendChatMessage,
  ChatApiError,
  type ChatMessage,
  type ChatSession,
} from "../../shared/api/chat";
import { useAuth } from "../auth";
import { useTranslation, type TranslationKey } from "../../shared/i18n";

const POLLING_INTERVAL_MS = 3000; // Poll every 3 seconds
const MESSAGE_PAGE_SIZE = 50;

interface ChatPanelProps {
  nanoId: string;
  onClose: () => void;
  onUnauthorized?: () => void;
}

interface ChatPanelState {
  session: ChatSession | null;
  messages: ChatMessage[];
  lastMessageTime: string | null;
  loading: boolean;
  error: string | null;
  isSubmitting: boolean;
  submitError: string | null;
  rateLimitRetryAfterSeconds: number | null;
}

/**
 * ChatPanel Component
 *
 * Displays a chat interface with:
 * - Session creation/reuse
 * - Message listing with polling (using since timestamp)
 * - Message composition
 * - Error/empty states
 * - Rate limiting feedback
 */
export function ChatPanel({ nanoId, onClose, onUnauthorized }: ChatPanelProps): JSX.Element {
  const { t } = useTranslation();
  const { user } = useAuth();
  const messageFieldId = useId();
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastMessageTimeRef = useRef<string | null>(null);
  const isActiveMountRef = useRef(true);

  const [state, setState] = useState<ChatPanelState>({
    session: null,
    messages: [],
    lastMessageTime: null,
    loading: true,
    error: null,
    isSubmitting: false,
    submitError: null,
    rateLimitRetryAfterSeconds: null,
  });

  const [messageDraft, setMessageDraft] = useState("");
  const [retryVersion, setRetryVersion] = useState(0);

  /**
   * Loads messages for a session, deduplicates against existing messages, and
   * advances the polling cursor (lastMessageTimeRef). Wrapped in useCallback so
   * that effects referencing it receive a stable identity when their deps hold.
   */
  const loadMessages = useCallback(async (sessionId: string, since: string | null): Promise<void> => {
    try {
      const response = await getChatMessages(sessionId, since || undefined, 1, MESSAGE_PAGE_SIZE);

      if (!isActiveMountRef.current) {
        return;
      }

      if (response.messages.length > 0) {
        setState((prev) => {
          const knownIds = new Set(prev.messages.map((message) => message.messageId));
          const newMessages = response.messages.filter((message) => !knownIds.has(message.messageId));
          const mergedMessages = newMessages.length > 0 ? [...prev.messages, ...newMessages] : prev.messages;
          const nextLastMessageTime = mergedMessages[mergedMessages.length - 1]?.createdAt ?? prev.lastMessageTime;

          lastMessageTimeRef.current = nextLastMessageTime;

          return {
            ...prev,
            messages: mergedMessages,
            lastMessageTime: nextLastMessageTime,
            error: null,
          };
        });
      }
    } catch (error) {
      if (!isActiveMountRef.current) {
        return;
      }

      // Don't show error for polling failures - just log silently
      if (error instanceof ChatApiError && error.code === "unauthorized") {
        if (onUnauthorized) {
          onUnauthorized();
          return;
        }

        setState((prev) => ({ ...prev, error: t("auth_error_unauthorized") }));
      }
    }
  }, [onUnauthorized, t]);

  // Initialize session on mount
  useEffect(() => {
    let isMounted = true;
    isActiveMountRef.current = true;

    const initializeSession = async (): Promise<void> => {
      try {
        setState((prev) => ({ ...prev, loading: true, error: null }));

        const response = await createChatSession({
          nanoId,
        });

        if (!isMounted || !isActiveMountRef.current) {
          return;
        }

        lastMessageTimeRef.current = null;
        setState((prev) => ({
          ...prev,
          session: response.session,
          messages: [],
          lastMessageTime: null,
          loading: false,
          submitError: null,
        }));

        // Load initial messages
        await loadMessages(response.session.sessionId, null);
      } catch (error) {
        if (!isMounted || !isActiveMountRef.current) {
          return;
        }

        if (error instanceof ChatApiError) {
          if (error.code === "unauthorized" && onUnauthorized) {
            onUnauthorized();
            return;
          }

          // Creator flow: session creation can be forbidden when no participant
          // has started a conversation yet. In this case, try to open an
          // existing session list filtered by nano.
          if (error.code === "forbidden") {
            try {
              const sessionsResponse = await listChatSessions(nanoId, 1, 50);
              const existingSession = sessionsResponse.sessions[0] ?? null;

              if (existingSession) {
                lastMessageTimeRef.current = null;
                setState((prev) => ({
                  ...prev,
                  session: existingSession,
                  messages: [],
                  lastMessageTime: null,
                  loading: false,
                  error: null,
                  submitError: null,
                }));

                await loadMessages(existingSession.sessionId, null);
                return;
              }

              setState((prev) => ({
                ...prev,
                session: null,
                messages: [],
                lastMessageTime: null,
                loading: false,
                error: null,
                submitError: t("chat_wait_for_first_participant_message"),
              }));
              return;
            } catch {
              // Fall through to default error handling below.
            }
          }

          const errorMessage = getErrorMessage(error, t);
          setState((prev) => ({ ...prev, error: errorMessage, loading: false }));
        } else {
          setState((prev) => ({
            ...prev,
            error: t("chat_error_generic"),
            loading: false,
          }));
        }
      }
    };

    void initializeSession();

    return () => {
      isMounted = false;
      isActiveMountRef.current = false;
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [nanoId, onUnauthorized, retryVersion, t, loadMessages]);

  // Polling effect
  useEffect(() => {
    if (!state.session || state.loading) {
      return;
    }

    const sessionId = state.session.sessionId;

    const poll = async (): Promise<void> => {
      if (!isActiveMountRef.current) {
        return;
      }

      try {
        await loadMessages(sessionId, lastMessageTimeRef.current);
      } catch {
        // Silent fail on poll errors - don't interrupt polling loop
      }
    };

    // Poll immediately, then set interval
    void poll();
    pollIntervalRef.current = setInterval(() => {
      void poll();
    }, POLLING_INTERVAL_MS);

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [state.loading, state.session, loadMessages]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [state.messages]);

  // Decrease active rate-limit backoff each second until input is enabled again.
  useEffect(() => {
    if (!state.rateLimitRetryAfterSeconds || state.rateLimitRetryAfterSeconds <= 0) {
      return;
    }

    const timer = setTimeout(() => {
      setState((prev) => {
        if (!prev.rateLimitRetryAfterSeconds || prev.rateLimitRetryAfterSeconds <= 1) {
          return {
            ...prev,
            rateLimitRetryAfterSeconds: null,
          };
        }

        return {
          ...prev,
          rateLimitRetryAfterSeconds: prev.rateLimitRetryAfterSeconds - 1,
        };
      });
    }, 1000);

    return () => {
      clearTimeout(timer);
    };
  }, [state.rateLimitRetryAfterSeconds]);

  const handleSendMessage = async (): Promise<void> => {
    if (!state.session) {
      setState((prev) => ({
        ...prev,
        submitError: t("chat_wait_for_first_participant_message"),
      }));
      return;
    }

    const trimmedContent = messageDraft.trim();

    if (!trimmedContent) {
      return;
    }

    setState((prev) => ({ ...prev, isSubmitting: true, submitError: null }));

    try {
      const response = await sendChatMessage(state.session.sessionId, {
        content: trimmedContent,
      });

      if (!isActiveMountRef.current) {
        return;
      }

      setState((prev) => {
        // Keep the polling cursor ref in sync with the latest sent message so
        // the next poll only fetches messages after this one.
        lastMessageTimeRef.current = response.message.createdAt;

        return {
          ...prev,
          messages: [...prev.messages, response.message],
          lastMessageTime: response.message.createdAt,
          isSubmitting: false,
        };
      });

      setMessageDraft("");
    } catch (error) {
      if (!isActiveMountRef.current) {
        return;
      }

      if (error instanceof ChatApiError) {
        if (error.code === "unauthorized" && onUnauthorized) {
          onUnauthorized();
          return;
        }

        if (error.code === "rate-limited") {
          setState((prev) => ({
            ...prev,
            submitError: getErrorMessage(error, t),
            isSubmitting: false,
            rateLimitRetryAfterSeconds: error.retryAfterSeconds,
          }));
          return;
        }

        const errorMessage = getErrorMessage(error, t);
        setState((prev) => ({ ...prev, submitError: errorMessage, isSubmitting: false }));
      } else {
        setState((prev) => ({
          ...prev,
          submitError: t("chat_error_send_failed"),
          isSubmitting: false,
        }));
      }
    }
  };

  if (state.loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
          <p className="text-neutral-700">{t("chat_loading")}</p>
        </div>
      </div>
    );
  }

  if (state.error) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6 space-y-4">
          <h2 className="text-lg font-semibold text-error-600">{t("chat_error_title")}</h2>
          <p className="text-neutral-700">{state.error}</p>
          <div className="flex gap-3">
            <button type="button" className="btn-outline flex-1" onClick={onClose}>
              {t("chat_close_button")}
            </button>
            <button
              type="button"
              className="btn-primary flex-1"
              onClick={() => {
                setState((prev) => ({ ...prev, loading: true, error: null }));
                setRetryVersion((current) => current + 1);
              }}
            >
              {t("chat_retry_button")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-end z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md h-[600px] max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-neutral-200 p-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-neutral-900">{t("chat_title")}</h2>
          <button
            type="button"
            className="p-2 hover:bg-neutral-100 rounded-md transition-colors"
            onClick={onClose}
            aria-label={t("chat_close_button")}
          >
            ✕
          </button>
        </div>

        {/* Messages Container */}
        <div
          ref={messagesContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-3"
          role="log"
          aria-label={t("chat_messages_label")}
        >
          {state.messages.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-sm text-neutral-600">{t("chat_no_messages")}</p>
            </div>
          ) : (
            state.messages.map((message) => (
              <div key={message.messageId} className="flex gap-2">
                <div className="flex-1">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="text-sm font-medium text-neutral-900">
                      {message.senderId === user?.id
                        ? t("chat_me")
                        : message.senderId === state.session?.creatorId
                          ? t("chat_sender_creator")
                          : t("chat_sender_participant")}
                    </span>
                    <span className="text-xs text-neutral-500">
                      {formatMessageTime(message.createdAt)}
                    </span>
                  </div>
                  <p className="text-sm text-neutral-700 mt-1 whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Footer - Message Input */}
        <div className="border-t border-neutral-200 p-4 space-y-3">
          {state.submitError && (
            <p className="text-sm text-error-600" role="alert">
              {state.submitError}
            </p>
          )}

          {state.rateLimitRetryAfterSeconds && (
            <p className="text-sm text-neutral-600" aria-live="polite">
              {t("chat_rate_limit_wait_prefix")} {state.rateLimitRetryAfterSeconds}
              {t("chat_rate_limit_wait_suffix")}
            </p>
          )}

          <div className="flex gap-2">
            <textarea
              id={messageFieldId}
              className="flex-1 min-h-12 max-h-24 rounded-md border border-neutral-300 px-3 py-2 text-sm resize-none focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-100"
              value={messageDraft}
              onChange={(e) => setMessageDraft(e.target.value)}
              placeholder={t("chat_message_placeholder")}
              disabled={state.isSubmitting || !state.session || state.rateLimitRetryAfterSeconds !== null}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void handleSendMessage();
                }
              }}
            />
            <button
              type="button"
              className="btn-primary px-4 self-end"
              onClick={() => {
                void handleSendMessage();
              }}
              disabled={
                state.isSubmitting
                || !state.session
                || messageDraft.trim().length === 0
                || state.rateLimitRetryAfterSeconds !== null
              }
              aria-label={t("chat_send_button")}
            >
              {state.isSubmitting
                ? t("chat_sending")
                : state.rateLimitRetryAfterSeconds
                  ? `${t("chat_send_button_wait_prefix")} ${state.rateLimitRetryAfterSeconds}s`
                  : t("chat_send_button")}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function getErrorMessage(error: ChatApiError, t: (key: TranslationKey) => string): string {
  switch (error.code) {
    case "unauthorized":
      return t("auth_error_unauthorized");
    case "forbidden":
      return t("auth_error_forbidden");
    case "not-found":
      return t("chat_error_session_not_found");
    case "rate-limited":
      return t("chat_error_rate_limited");
    case "validation":
      return t("chat_error_validation");
    case "conflict":
      return t("chat_error_conflict");
    default:
      return t("chat_error_generic");
  }
}

function formatMessageTime(timestamp: string): string {
  const date = new Date(timestamp);

  // Guard against invalid date inputs: new Date() does not throw, but produces
  // an invalid Date whose time value is NaN. Return an empty string to avoid
  // showing "Invalid Date" to users.
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString([], {
    hour: "2-digit",
    minute: "2-digit",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

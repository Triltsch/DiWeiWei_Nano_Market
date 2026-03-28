import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { ChatPanel } from "./ChatPanel";
import * as chatApi from "../../shared/api/chat";
import { ChatApiError } from "../../shared/api/chat";

// Mock the chat API
vi.mock("../../shared/api/chat");
vi.mock("../auth", () => ({
  useAuth: () => ({ user: { id: "participant-1" }, isAuthenticated: true }),
}));
vi.mock("../../shared/i18n", () => ({
  useTranslation: () => ({
    t: (key: string) => key,
    language: "en",
  }),
}));

const mockChatApi = vi.mocked(chatApi);

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false });
    vi.clearAllMocks();

    // Set up default mock implementations
    mockChatApi.createChatSession.mockResolvedValue({
      session: {
        sessionId: "session-1",
        nanoId: "nano-1",
        creatorId: "creator-1",
        participantUserId: "participant-1",
        counterpartUserId: "creator-1",
        createdAt: "2026-03-27T10:00:00Z",
        updatedAt: "2026-03-27T10:00:00Z",
        lastMessageAt: null,
      },
      meta: {},
    });

    mockChatApi.getChatMessages.mockResolvedValue({
      messages: [
        {
          messageId: "msg-1",
          sessionId: "session-1",
          senderId: "creator-1",
          content: "Hello from creator",
          createdAt: "2026-03-27T10:00:00Z",
          updatedAt: "2026-03-27T10:00:00Z",
        },
      ],
      pagination: {
        current_page: 1,
        page_size: 50,
        total_results: 1,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });

    mockChatApi.sendChatMessage.mockResolvedValue({
      message: {
        messageId: "msg-2",
        sessionId: "session-1",
        senderId: "participant-1",
        content: "My response",
        createdAt: "2026-03-27T10:05:00Z",
        updatedAt: "2026-03-27T10:05:00Z",
      },
    });
  });

  afterEach(() => {
    vi.useRealTimers();
    cleanup();
  });

  it("should initialize chat session on mount", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalledWith({
        nanoId: "nano-1",
      });
    });
  });

  it("should display loading state initially", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    expect(screen.getByText("chat_loading")).toBeInTheDocument();
  });

  it("should load and display messages after session creation", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("Hello from creator")).toBeInTheDocument();
    });
  });

  it("should display error state on session creation failure", async () => {
    mockChatApi.createChatSession.mockRejectedValueOnce(
      new ChatApiError("Session creation failed", "request-failed"),
    );

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("chat_error_title")).toBeInTheDocument();
    });
  });

  it("should fallback to existing session list when create session is forbidden", async () => {
    mockChatApi.createChatSession.mockRejectedValueOnce(
      new ChatApiError("Forbidden", "forbidden"),
    );

    mockChatApi.listChatSessions.mockResolvedValueOnce({
      sessions: [
        {
          sessionId: "session-existing",
          nanoId: "nano-1",
          creatorId: "creator-1",
          participantUserId: "participant-1",
          counterpartUserId: "participant-1",
          createdAt: "2026-03-27T10:00:00Z",
          updatedAt: "2026-03-27T10:00:00Z",
          lastMessageAt: null,
        },
      ],
      pagination: {
        current_page: 1,
        page_size: 50,
        total_results: 1,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.listChatSessions).toHaveBeenCalledWith("nano-1", 1, 50);
    });

    await waitFor(() => {
      expect(mockChatApi.getChatMessages).toHaveBeenCalledWith("session-existing", undefined, 1, 50);
    });
  });

  it("should send message on button click", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const textarea = screen.getByPlaceholderText("chat_message_placeholder");
    const sendButton = screen.getByRole("button", { name: "chat_send_button" });

    fireEvent.change(textarea, { target: { value: "Test message" } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(mockChatApi.sendChatMessage).toHaveBeenCalledWith("session-1", {
        content: "Test message",
      });
    });
  });

  it("should send message on Enter key (without Shift)", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const textarea = screen.getByPlaceholderText("chat_message_placeholder");

    fireEvent.change(textarea, { target: { value: "Test message" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    await waitFor(() => {
      expect(mockChatApi.sendChatMessage).toHaveBeenCalledWith("session-1", {
        content: "Test message",
      });
    });
  });

  it("should clear message input after successful send", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const textarea = screen.getByPlaceholderText("chat_message_placeholder") as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: "Test message" } });
    fireEvent.click(screen.getByRole("button", { name: "chat_send_button" }));

    await waitFor(() => {
      expect(textarea.value).toBe("");
    });
  });

  it("should display error when message send fails", async () => {
    mockChatApi.sendChatMessage.mockRejectedValueOnce(
      new ChatApiError("Rate limited", "rate-limited"),
    );

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const textarea = screen.getByPlaceholderText("chat_message_placeholder");
    fireEvent.change(textarea, { target: { value: "Test message" } });
    fireEvent.click(screen.getByRole("button", { name: "chat_send_button" }));

    await waitFor(() => {
      expect(screen.getByText("chat_error_rate_limited")).toBeInTheDocument();
    });
  });

  it("should call onClose when close button is clicked", async () => {
    const onClose = vi.fn();

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={onClose}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const closeButton = screen.getByRole("button", { name: "chat_close_button" });
    fireEvent.click(closeButton);

    expect(onClose).toHaveBeenCalled();
  });

  it("should display empty state when no messages", async () => {
    mockChatApi.getChatMessages.mockResolvedValueOnce({
      messages: [],
      pagination: {
        current_page: 1,
        page_size: 50,
        total_results: 0,
        total_pages: 1,
        has_next_page: false,
        has_prev_page: false,
      },
    });

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("chat_no_messages")).toBeInTheDocument();
    });
  });

  it("should disable send button when message is empty", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const sendButton = screen.getByRole("button", { name: "chat_send_button" });

    expect(sendButton).toBeDisabled();
  });

  it("should enable send button when message has content", async () => {
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const textarea = screen.getByPlaceholderText("chat_message_placeholder");
    fireEvent.change(textarea, { target: { value: "Test message" } });

    const sendButton = screen.getByRole("button", { name: "chat_send_button" });

    await waitFor(() => {
      expect(sendButton).not.toBeDisabled();
    });
  });

  it("should display role-based sender labels for each message", async () => {
    // The default mock sends a message from "creator-1"; current user is "participant-1".
    // Expect the creator's message to be labelled with the creator role label.
    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
      />,
    );

    await waitFor(() => {
      expect(screen.getByText("chat_sender_creator")).toBeInTheDocument();
    });
  });

  it("should trigger unauthorized callback on session creation 401", async () => {
    const onUnauthorized = vi.fn();
    mockChatApi.createChatSession.mockRejectedValueOnce(
      new ChatApiError("Unauthorized", "unauthorized"),
    );

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
        onUnauthorized={onUnauthorized}
      />,
    );

    await waitFor(() => {
      expect(onUnauthorized).toHaveBeenCalledTimes(1);
    });
  });

  it("should trigger unauthorized callback on message send 401", async () => {
    const onUnauthorized = vi.fn();
    mockChatApi.sendChatMessage.mockRejectedValueOnce(
      new ChatApiError("Unauthorized", "unauthorized"),
    );

    render(
      <ChatPanel
        nanoId="nano-1"
        onClose={() => {}}
        onUnauthorized={onUnauthorized}
      />,
    );

    await waitFor(() => {
      expect(mockChatApi.createChatSession).toHaveBeenCalled();
    });

    const textarea = screen.getByPlaceholderText("chat_message_placeholder");
    fireEvent.change(textarea, { target: { value: "Test message" } });
    fireEvent.click(screen.getByRole("button", { name: "chat_send_button" }));

    await waitFor(() => {
      expect(onUnauthorized).toHaveBeenCalledTimes(1);
    });
  });
});

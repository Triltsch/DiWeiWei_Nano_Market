import axios from "axios";

import { httpClient } from "./httpClient";
import type { PaginationMeta } from "./creator";

export interface ChatSession {
  sessionId: string;
  nanoId: string;
  creatorId: string;
  participantUserId: string;
  counterpartUserId: string;
  createdAt: string;
  updatedAt: string;
  lastMessageAt: string | null;
}

export interface ChatSessionCreateRequest {
  nanoId: string;
}

export interface ChatSessionCreateResponse {
  session: ChatSession;
  meta: Record<string, unknown>;
}

export interface ChatSessionListResponse {
  sessions: ChatSession[];
  pagination: PaginationMeta;
}

export interface ChatMessage {
  messageId: string;
  sessionId: string;
  senderId: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessageCreateRequest {
  content: string;
}

export interface ChatMessageCreateResponse {
  message: ChatMessage;
}

export interface ChatMessageListResponse {
  messages: ChatMessage[];
  pagination: PaginationMeta;
}

type ChatApiErrorCode =
  | "not-found"
  | "unauthorized"
  | "forbidden"
  | "conflict"
  | "validation"
  | "rate-limited"
  | "request-failed"
  | "unknown";

interface ErrorResponseBody {
  detail?: string;
}

interface RawChatSession {
  session_id?: unknown;
  nano_id?: unknown;
  creator_id?: unknown;
  participant_user_id?: unknown;
  counterpart_user_id?: unknown;
  created_at?: unknown;
  updated_at?: unknown;
  last_message_at?: unknown;
}

/** @deprecated Use RawChatSession directly; kept as alias for backward source compatibility. */
type RawChatSessionData = RawChatSession;

interface RawChatSessionResponse {
  data?: unknown;
  meta?: unknown;
}

interface RawPaginationMeta {
  current_page?: unknown;
  page_size?: unknown;
  total_results?: unknown;
  total_pages?: unknown;
  has_next_page?: unknown;
  has_prev_page?: unknown;
}

interface RawChatSessionsData {
  data?: unknown;
  meta?: unknown;
}

interface RawChatSessionsResponse {
  data?: unknown;
}

interface RawChatMessage {
  message_id?: unknown;
  session_id?: unknown;
  sender_id?: unknown;
  content?: unknown;
  created_at?: unknown;
  updated_at?: unknown;
}

/** @deprecated Use RawChatMessage directly; kept as alias for backward source compatibility. */
type RawChatMessageData = RawChatMessage;

interface RawChatMessageResponse {
  data?: unknown;
}

interface RawChatMessagesData {
  data?: unknown;
  meta?: unknown;
}

interface RawChatMessagesResponse {
  data?: unknown;
}

function asString(value: unknown): string | null {
  if (typeof value === "string" && value.trim().length > 0) {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return null;
}

function asNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string" && value.trim().length > 0) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}

function asBoolean(value: unknown): boolean {
  return value === true;
}

function mapPagination(raw: RawPaginationMeta | undefined, fallbackCount: number): PaginationMeta {
  return {
    current_page: asNumber(raw?.current_page) ?? 1,
    page_size: asNumber(raw?.page_size) ?? fallbackCount,
    total_results: asNumber(raw?.total_results) ?? fallbackCount,
    total_pages: asNumber(raw?.total_pages) ?? 1,
    has_next_page: asBoolean(raw?.has_next_page),
    has_prev_page: asBoolean(raw?.has_prev_page),
  };
}

function mapChatSession(raw: RawChatSession | undefined, index: number): ChatSession {
  return {
    sessionId: asString(raw?.session_id) ?? `session-${index}`,
    nanoId: asString(raw?.nano_id) ?? "",
    creatorId: asString(raw?.creator_id) ?? "",
    participantUserId: asString(raw?.participant_user_id) ?? "",
    counterpartUserId: asString(raw?.counterpart_user_id) ?? "",
    createdAt: asString(raw?.created_at) ?? "",
    updatedAt: asString(raw?.updated_at) ?? "",
    lastMessageAt: asString(raw?.last_message_at),
  };
}

function mapChatMessage(raw: RawChatMessage | undefined, index: number): ChatMessage {
  return {
    messageId: asString(raw?.message_id) ?? `message-${index}`,
    sessionId: asString(raw?.session_id) ?? "",
    senderId: asString(raw?.sender_id) ?? "",
    content: asString(raw?.content) ?? "",
    createdAt: asString(raw?.created_at) ?? "",
    updatedAt: asString(raw?.updated_at) ?? "",
  };
}

function getErrorCode(error: unknown): ChatApiErrorCode {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const status = error.response?.status;

    if (status === 404) {
      return "not-found";
    }
    if (status === 401) {
      return "unauthorized";
    }
    if (status === 403) {
      return "forbidden";
    }
    if (status === 409) {
      return "conflict";
    }
    if (status === 422) {
      return "validation";
    }
    if (status === 429) {
      return "rate-limited";
    }
    if (status) {
      return "request-failed";
    }
  }

  return "unknown";
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ErrorResponseBody>(error)) {
    const detail = error.response?.data?.detail;
    if (detail && detail.trim().length > 0) {
      return detail;
    }
    return "Request failed";
  }

  if (error instanceof Error && error.message.trim().length > 0) {
    return error.message;
  }

  return "Request failed";
}

export class ChatApiError extends Error {
  code: ChatApiErrorCode;

  constructor(message: string, code: ChatApiErrorCode) {
    super(message);
    this.name = "ChatApiError";
    this.code = code;
  }
}

export async function createChatSession(
  payload: ChatSessionCreateRequest,
): Promise<ChatSessionCreateResponse> {
  try {
    const response = await httpClient.post<RawChatSessionResponse>(
      "/api/v1/chats",
      { nano_id: payload.nanoId },
    );
    const rawData = (response.data.data as RawChatSessionData | undefined) ?? {};

    return {
      session: mapChatSession(rawData as RawChatSession | undefined, 0),
      meta: (response.data.meta as Record<string, unknown>) ?? {},
    };
  } catch (error) {
    throw new ChatApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function listChatSessions(
  nanoId?: string,
  page: number = 1,
  limit: number = 50,
): Promise<ChatSessionListResponse> {
  try {
    const response = await httpClient.get<RawChatSessionsResponse>("/api/v1/chats", {
      params: {
        ...(nanoId ? { nano_id: nanoId } : {}),
        page,
        limit,
      },
    });
    const rawData = (response.data as RawChatSessionsData | undefined) ?? {};

    const sessions = Array.isArray(rawData.data)
      ? (rawData.data as RawChatSession[]).map(mapChatSession)
      : [];

    return {
      sessions,
      pagination: mapPagination(rawData.meta as RawPaginationMeta | undefined, sessions.length),
    };
  } catch (error) {
    throw new ChatApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function sendChatMessage(
  sessionId: string,
  payload: ChatMessageCreateRequest,
): Promise<ChatMessageCreateResponse> {
  try {
    const response = await httpClient.post<RawChatMessageResponse>(
      `/api/v1/chats/${sessionId}/messages`,
      payload,
    );
    const rawData = (response.data.data as RawChatMessageData | undefined) ?? {};

    return {
      message: mapChatMessage(rawData as RawChatMessage | undefined, 0),
    };
  } catch (error) {
    throw new ChatApiError(getErrorMessage(error), getErrorCode(error));
  }
}

export async function getChatMessages(
  sessionId: string,
  since?: string,
  page: number = 1,
  limit: number = 50,
): Promise<ChatMessageListResponse> {
  try {
    const response = await httpClient.get<RawChatMessagesResponse>(
      `/api/v1/chats/${sessionId}/messages`,
      {
        params: {
          ...(since ? { since } : {}),
          page,
          limit,
        },
      },
    );
    const rawData = (response.data as RawChatMessagesData | undefined) ?? {};

    const messages = Array.isArray(rawData.data)
      ? (rawData.data as RawChatMessage[]).map(mapChatMessage)
      : [];

    return {
      messages,
      pagination: mapPagination(rawData.meta as RawPaginationMeta | undefined, messages.length),
    };
  } catch (error) {
    throw new ChatApiError(getErrorMessage(error), getErrorCode(error));
  }
}

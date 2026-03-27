import axios from "axios";
import { describe, it, expect, vi, beforeEach, type Mock } from "vitest";

import { httpClient } from "./httpClient";
import {
  createChatSession,
  getChatMessages,
  listChatSessions,
  sendChatMessage,
  ChatApiError,
  type ChatSession,
  type ChatMessage,
} from "./chat";

vi.mock("./httpClient");

const mockHttpClient = vi.mocked(httpClient);
const mockHttpGet = httpClient.get as unknown as Mock;
const mockHttpPost = httpClient.post as unknown as Mock;

const mockSession: ChatSession = {
  sessionId: "session-1",
  nanoId: "nano-1",
  creatorId: "creator-1",
  participantUserId: "participant-1",
  counterpartUserId: "creator-1",
  createdAt: "2026-03-27T10:00:00Z",
  updatedAt: "2026-03-27T10:00:00Z",
  lastMessageAt: null,
};

const mockMessage: ChatMessage = {
  messageId: "msg-1",
  sessionId: "session-1",
  senderId: "sender-1",
  content: "Hello, world!",
  createdAt: "2026-03-27T10:05:00Z",
  updatedAt: "2026-03-27T10:05:00Z",
};

describe("Chat API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("createChatSession", () => {
    it("should create a new chat session successfully", async () => {
      const mockResponse = {
        data: {
          data: {
            session_id: mockSession.sessionId,
            nano_id: mockSession.nanoId,
            creator_id: mockSession.creatorId,
            participant_user_id: mockSession.participantUserId,
            counterpart_user_id: mockSession.counterpartUserId,
            created_at: mockSession.createdAt,
            updated_at: mockSession.updatedAt,
            last_message_at: mockSession.lastMessageAt,
          },
          meta: {
            reused: false,
          },
        },
      };

      mockHttpPost.mockResolvedValueOnce(mockResponse);

      const result = await createChatSession({
        nanoId: "nano-1",
      });

      expect(result.session.sessionId).toBe(mockSession.sessionId);
      expect(result.meta.reused).toBe(false);
      expect(mockHttpClient.post).toHaveBeenCalledWith("/api/v1/chats", {
        nano_id: "nano-1",
      });
    });

    it("should throw ChatApiError on unauthorized", async () => {
      const error = new axios.AxiosError();
      error.response = { status: 401, data: { detail: "Unauthorized" } } as any;

      mockHttpPost.mockRejectedValueOnce(error);

      await expect(
        createChatSession({
          nanoId: "nano-1",
        }),
      ).rejects.toThrow(ChatApiError);
    });
  });

  describe("listChatSessions", () => {
    it("should list chat sessions successfully", async () => {
      const mockResponse = {
        data: {
          data: [
            {
              session_id: mockSession.sessionId,
              nano_id: mockSession.nanoId,
              creator_id: mockSession.creatorId,
              participant_user_id: mockSession.participantUserId,
              counterpart_user_id: mockSession.counterpartUserId,
              created_at: mockSession.createdAt,
              updated_at: mockSession.updatedAt,
              last_message_at: mockSession.lastMessageAt,
            },
          ],
          meta: {
            current_page: 1,
            page_size: 50,
            total_results: 1,
            total_pages: 1,
            has_next_page: false,
            has_prev_page: false,
          },
        },
      };

      mockHttpGet.mockResolvedValueOnce(mockResponse);

      const result = await listChatSessions("nano-1", 1, 50);

      expect(result.sessions).toHaveLength(1);
      expect(result.sessions[0].sessionId).toBe(mockSession.sessionId);
      expect(result.pagination.total_results).toBe(1);
    });

    it("should handle rate limiting (429)", async () => {
      const error = new axios.AxiosError();
      error.response = {
        status: 429,
        data: { detail: "Rate limited" },
      } as any;

      mockHttpGet.mockRejectedValueOnce(error);

      await expect(listChatSessions("nano-1")).rejects.toThrow(ChatApiError);
    });
  });

  describe("sendChatMessage", () => {
    it("should send a message successfully", async () => {
      const mockResponse = {
        data: {
          data: {
            message_id: mockMessage.messageId,
            session_id: mockMessage.sessionId,
            sender_id: mockMessage.senderId,
            content: mockMessage.content,
            created_at: mockMessage.createdAt,
            updated_at: mockMessage.updatedAt,
          },
        },
      };

      mockHttpPost.mockResolvedValueOnce(mockResponse);

      const result = await sendChatMessage("session-1", {
        content: "Hello, world!",
      });

      expect(result.message.content).toBe(mockMessage.content);
      expect(mockHttpClient.post).toHaveBeenCalledWith(
        "/api/v1/chats/session-1/messages",
        { content: "Hello, world!" },
      );
    });

    it("should throw ChatApiError on validation error", async () => {
      const error = new axios.AxiosError();
      error.response = {
        status: 422,
        data: { detail: "Message is empty" },
      } as any;

      mockHttpPost.mockRejectedValueOnce(error);

      await expect(
        sendChatMessage("session-1", { content: "" }),
      ).rejects.toThrow(ChatApiError);
    });
  });

  describe("getChatMessages", () => {
    it("should get messages with polling", async () => {
      const mockResponse = {
        data: {
          data: [
            {
              message_id: mockMessage.messageId,
              session_id: mockMessage.sessionId,
              sender_id: mockMessage.senderId,
              content: mockMessage.content,
              created_at: mockMessage.createdAt,
              updated_at: mockMessage.updatedAt,
            },
          ],
          meta: {
            current_page: 1,
            page_size: 50,
            total_results: 1,
            total_pages: 1,
            has_next_page: false,
            has_prev_page: false,
          },
        },
      };

      mockHttpGet.mockResolvedValueOnce(mockResponse);

      const since = "2026-03-27T10:00:00Z";
      const result = await getChatMessages("session-1", since, 1, 50);

      expect(result.messages).toHaveLength(1);
      expect(result.messages[0].content).toBe(mockMessage.content);
      expect(mockHttpClient.get).toHaveBeenCalledWith("/api/v1/chats/session-1/messages", {
        params: {
          since,
          page: 1,
          limit: 50,
        },
      });
    });

    it("should get messages without since parameter", async () => {
      const mockResponse = {
        data: {
          data: [],
          meta: {
            current_page: 1,
            page_size: 50,
            total_results: 0,
            total_pages: 1,
            has_next_page: false,
            has_prev_page: false,
          },
        },
      };

      mockHttpGet.mockResolvedValueOnce(mockResponse);

      const result = await getChatMessages("session-1", undefined, 1, 50);

      expect(result.messages).toHaveLength(0);
      expect(mockHttpClient.get).toHaveBeenCalledWith("/api/v1/chats/session-1/messages", {
        params: {
          page: 1,
          limit: 50,
        },
      });
    });
  });

  describe("ChatApiError", () => {
    it("should create error with correct code", () => {
      const error = new ChatApiError("Test error", "rate-limited");

      expect(error.message).toBe("Test error");
      expect(error.code).toBe("rate-limited");
      expect(error.name).toBe("ChatApiError");
    });
  });
});

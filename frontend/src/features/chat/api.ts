// Chat API helpers and React Query hooks for SPEC-304 screens.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import {
  ChatConversation,
  ChatConversationListResponse,
  ChatMemberListResponse,
  ChatMessage,
  ChatMessageListResponse,
} from "./types";

const chatStaleTimeMs = 10_000;

/** Build a stable query key for one organization's chat members. */
export function chatMembersQueryKey(organizationId: string) {
  return ["organizations", organizationId, "chat", "members"] as const;
}

/** Build a stable query key for one organization's chat conversation list. */
export function chatConversationsQueryKey(organizationId: string) {
  return ["organizations", organizationId, "chat", "conversations"] as const;
}

/** Build a stable query key for one conversation history. */
export function chatMessagesQueryKey(conversationId: string) {
  return ["chat", "conversations", conversationId, "messages"] as const;
}

/** Fetch internal organization members visible in chat. */
export function listChatMembers(organizationId: string) {
  return apiRequest<ChatMemberListResponse>(
    `/api/v1/organizations/${organizationId}/chat/members`,
  );
}

/** Fetch current-user conversations for one organization. */
export function listChatConversations(organizationId: string) {
  return apiRequest<ChatConversationListResponse>(
    `/api/v1/organizations/${organizationId}/chat/conversations`,
  );
}

/** Create or return a direct conversation with one organization member. */
export function createDirectConversation(
  organizationId: string,
  targetUserId: string,
) {
  return apiRequest<ChatConversation>(
    `/api/v1/organizations/${organizationId}/chat/direct-conversations`,
    {
      method: "POST",
      body: JSON.stringify({ target_user_id: targetUserId }),
    },
  );
}

/** Create or return the project channel for one accessible project. */
export function getProjectChatChannel(projectId: string) {
  return apiRequest<ChatConversation>(
    `/api/v1/projects/${projectId}/chat/channel`,
  );
}

/** Fetch visible message history for one conversation. */
export function listChatMessages(conversationId: string) {
  return apiRequest<ChatMessageListResponse>(
    `/api/v1/chat/conversations/${conversationId}/messages?limit=100&offset=0`,
  );
}

/** Persist a chat message through the REST fallback path. */
export function sendChatMessage(conversationId: string, body: string) {
  return apiRequest<ChatMessage>(
    `/api/v1/chat/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ body }),
    },
  );
}

/** Mark one conversation read for the current participant. */
export function markChatRead(conversationId: string) {
  return apiRequest<ChatConversation>(
    `/api/v1/chat/conversations/${conversationId}/read`,
    { method: "POST" },
  );
}

/** Clear a conversation from the current participant's view. */
export function clearChatConversation(conversationId: string) {
  return apiRequest<ChatConversation>(
    `/api/v1/chat/conversations/${conversationId}/clear`,
    { method: "POST" },
  );
}

/** Keep chat members in React Query cache. */
export function useChatMembers(organizationId: string | undefined) {
  return useQuery({
    queryKey: organizationId
      ? chatMembersQueryKey(organizationId)
      : ["organizations", "missing", "chat", "members"],
    queryFn: () => listChatMembers(organizationId ?? ""),
    enabled: Boolean(organizationId),
    staleTime: chatStaleTimeMs,
  });
}

/** Keep conversation summaries in React Query cache. */
export function useChatConversations(organizationId: string | undefined) {
  return useQuery({
    queryKey: organizationId
      ? chatConversationsQueryKey(organizationId)
      : ["organizations", "missing", "chat", "conversations"],
    queryFn: () => listChatConversations(organizationId ?? ""),
    enabled: Boolean(organizationId),
    staleTime: chatStaleTimeMs,
  });
}

/** Keep one conversation history in React Query cache. */
export function useChatMessages(conversationId: string | undefined) {
  return useQuery({
    queryKey: conversationId
      ? chatMessagesQueryKey(conversationId)
      : ["chat", "conversations", "missing", "messages"],
    queryFn: () => listChatMessages(conversationId ?? ""),
    enabled: Boolean(conversationId),
    staleTime: chatStaleTimeMs,
  });
}

/** Create direct conversations and refresh the organization's chat list. */
export function useCreateDirectConversation(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (targetUserId: string) =>
      createDirectConversation(organizationId, targetUserId),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({
        queryKey: chatConversationsQueryKey(organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: chatMessagesQueryKey(conversation.id),
      });
    },
  });
}

/** Open project channels and refresh the organization's chat list. */
export function useProjectChatChannel(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string) => getProjectChatChannel(projectId),
    onSuccess: (conversation) => {
      queryClient.invalidateQueries({
        queryKey: chatConversationsQueryKey(organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: chatMessagesQueryKey(conversation.id),
      });
    },
  });
}

/** Send messages through REST and refresh history when WebSocket is unavailable. */
export function useSendChatMessage(
  organizationId: string,
  conversationId: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => sendChatMessage(conversationId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: chatMessagesQueryKey(conversationId),
      });
      queryClient.invalidateQueries({
        queryKey: chatConversationsQueryKey(organizationId),
      });
    },
  });
}

/** Clear a conversation and refresh list/history state. */
export function useClearChatConversation(
  organizationId: string,
  conversationId: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => clearChatConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: chatConversationsQueryKey(organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: chatMessagesQueryKey(conversationId),
      });
    },
  });
}

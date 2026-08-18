// Organization chat page with member discovery, history, and WebSocket state.

import {
  Eraser,
  MessageCircle,
  RefreshCcw,
  Send,
  UsersRound,
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useParams, useSearchParams } from "react-router-dom";

import { getErrorMessage } from "../../shared/api";
import { useSession } from "../auth/session";
import {
  chatConversationsQueryKey,
  chatMessagesQueryKey,
  markChatRead,
  useChatConversations,
  useChatMembers,
  useChatMessages,
  useClearChatConversation,
  useCreateDirectConversation,
  useProjectChatChannel,
  useSendChatMessage,
} from "./api";
import { ChatConversation, ChatMessage } from "./types";
import { useOrganizationProjects } from "../projects/api";

type ConnectionState = "connecting" | "connected" | "reconnecting" | "failed";

/** Format timestamps for compact chat message metadata. */
function formatChatTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

/** Return a short human label for one conversation type. */
function conversationLabel(conversation: ChatConversation | undefined) {
  if (!conversation) {
    return "Select a conversation";
  }
  if (conversation.conversation_type === "organization_channel") {
    return "Organization channel";
  }
  if (conversation.conversation_type === "project_channel") {
    return "Project channel";
  }
  return "Direct message";
}

/** Derive the WebSocket URL from the current browser origin. */
function chatSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1/chat/ws`;
}

/** Render the authenticated organization chat page. */
export function OrganizationChatPage() {
  const { organizationId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedConversationId = searchParams.get("conversation") ?? undefined;
  const { data: user } = useSession();
  const queryClient = useQueryClient();
  const members = useChatMembers(organizationId);
  const conversations = useChatConversations(organizationId);
  const projects = useOrganizationProjects(organizationId, {
    limit: 100,
    offset: 0,
  });
  const messages = useChatMessages(selectedConversationId);
  const createDirect = useCreateDirectConversation(organizationId ?? "");
  const openProjectChannel = useProjectChatChannel(organizationId ?? "");
  const sendRest = useSendChatMessage(
    organizationId ?? "",
    selectedConversationId ?? "",
  );
  const clearConversation = useClearChatConversation(
    organizationId ?? "",
    selectedConversationId ?? "",
  );
  const [composer, setComposer] = useState("");
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("connecting");
  const [socketError, setSocketError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  const selectedConversation = useMemo(
    () =>
      conversations.data?.items.find(
        (conversation) => conversation.id === selectedConversationId,
      ),
    [conversations.data?.items, selectedConversationId],
  );

  useEffect(() => {
    if (!selectedConversationId) {
      return;
    }
    void markChatRead(selectedConversationId).then(() => {
      if (organizationId) {
        void queryClient.invalidateQueries({
          queryKey: chatConversationsQueryKey(organizationId),
        });
      }
    });
  }, [organizationId, queryClient, selectedConversationId]);

  useEffect(() => {
    if (!selectedConversationId) {
      socketRef.current?.close();
      socketRef.current = null;
      setConnectionState("failed");
      return;
    }
    setConnectionState((previous) =>
      previous === "connected" ? "reconnecting" : "connecting",
    );
    setSocketError(null);
    const socket = new WebSocket(chatSocketUrl());
    socketRef.current = socket;
    socket.addEventListener("open", () => {
      setConnectionState("connected");
      socket.send(
        JSON.stringify({
          type: "subscribe",
          conversation_id: selectedConversationId,
        }),
      );
    });
    socket.addEventListener("message", (event) => {
      const data = JSON.parse(event.data) as {
        type?: string;
        message?: ChatMessage;
        code?: string;
      };
      if (data.type === "message.created" && data.message) {
        queryClient.setQueryData(
          chatMessagesQueryKey(selectedConversationId),
          (
            current:
              | {
                  items: ChatMessage[];
                  total: number;
                  limit: number;
                  offset: number;
                }
              | undefined,
          ) => {
            if (!current) {
              return current;
            }
            if (
              current.items.some((message) => message.id === data.message?.id)
            ) {
              return current;
            }
            return {
              ...current,
              items: [...current.items, data.message],
              total: current.total + 1,
            };
          },
        );
        if (organizationId) {
          void queryClient.invalidateQueries({
            queryKey: chatConversationsQueryKey(organizationId),
          });
        }
      }
      if (data.type === "error") {
        setSocketError(data.code ?? "invalid_message");
      }
    });
    socket.addEventListener("close", () => {
      setConnectionState("failed");
      void queryClient.invalidateQueries({
        queryKey: chatMessagesQueryKey(selectedConversationId),
      });
    });
    return () => {
      socket.close();
    };
  }, [organizationId, queryClient, selectedConversationId]);

  /** Select a conversation by storing it in the route query string. */
  function selectConversation(conversationId: string) {
    const next = new URLSearchParams(searchParams);
    next.set("conversation", conversationId);
    setSearchParams(next);
  }

  /** Start or open a direct conversation with one member. */
  async function handleDirect(targetUserId: string) {
    const conversation = await createDirect.mutateAsync(targetUserId);
    selectConversation(conversation.id);
  }

  /** Open or create the channel for one accessible project. */
  async function handleProjectChannel(projectId: string) {
    const conversation = await openProjectChannel.mutateAsync(projectId);
    selectConversation(conversation.id);
  }

  /** Send through WebSocket when connected, otherwise use the REST fallback. */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const body = composer.trim();
    if (!body || !selectedConversationId) {
      return;
    }
    setComposer("");
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: "message.send",
          conversation_id: selectedConversationId,
          body,
        }),
      );
      return;
    }
    await sendRest.mutateAsync(body);
  }

  if (!organizationId) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Organization not found.
      </p>
    );
  }

  if (members.isLoading || conversations.isLoading || projects.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading chat.
      </p>
    );
  }

  if (members.isError || conversations.isError || projects.isError) {
    return (
      <p
        role="alert"
        className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
      >
        {getErrorMessage(
          members.error ?? conversations.error ?? projects.error,
        )}
      </p>
    );
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Chat</h1>
          <p className="text-sm text-muted">
            {conversationLabel(selectedConversation)}
          </p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm">
          <span
            className={`h-2 w-2 rounded-full ${
              connectionState === "connected" ? "bg-green-600" : "bg-accent"
            }`}
          />
          {connectionState === "connected"
            ? "Connected"
            : connectionState === "reconnecting"
              ? "Reconnecting"
              : selectedConversationId
                ? "Disconnected"
                : "No conversation"}
        </div>
      </div>

      <div className="grid min-h-[620px] gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4 rounded-md border border-line bg-white p-4">
          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <UsersRound aria-hidden="true" className="h-4 w-4 text-brand" />
              Members
            </h2>
            <div className="mt-3 space-y-2">
              {members.data?.items.map((member) => (
                <button
                  key={member.user_id}
                  type="button"
                  disabled={
                    member.user_id === user?.id || createDirect.isPending
                  }
                  className="w-full rounded-md border border-line px-3 py-2 text-left text-sm hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={() => void handleDirect(member.user_id)}
                >
                  <span className="block font-medium">{member.full_name}</span>
                  <span className="block text-xs text-muted">
                    {member.email}
                  </span>
                  {member.shares_project ? (
                    <span className="mt-1 inline-flex rounded-md bg-green-50 px-2 py-0.5 text-xs font-medium text-brand">
                      Shared project
                    </span>
                  ) : null}
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-line pt-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <MessageCircle
                aria-hidden="true"
                className="h-4 w-4 text-brand"
              />
              Project channels
            </h2>
            <div className="mt-3 space-y-2">
              {projects.data?.items.map((project) => (
                <button
                  key={project.id}
                  type="button"
                  disabled={openProjectChannel.isPending}
                  className="w-full rounded-md border border-line px-3 py-2 text-left text-sm hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={() => void handleProjectChannel(project.id)}
                >
                  <span className="block font-medium">{project.name}</span>
                  <span className="block text-xs text-muted">
                    Project channel
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="border-t border-line pt-4">
            <h2 className="flex items-center gap-2 text-sm font-semibold">
              <MessageCircle
                aria-hidden="true"
                className="h-4 w-4 text-brand"
              />
              Conversations
            </h2>
            <div className="mt-3 space-y-2">
              {conversations.data?.items.map((conversation) => (
                <button
                  key={conversation.id}
                  type="button"
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm ${
                    conversation.id === selectedConversationId
                      ? "border-brand bg-green-50"
                      : "border-line hover:bg-surface"
                  }`}
                  onClick={() => selectConversation(conversation.id)}
                >
                  <span className="font-medium">
                    {conversationLabel(conversation)}
                  </span>
                  {conversation.unread_count > 0 ? (
                    <span className="ml-2 rounded-full bg-brand px-2 py-0.5 text-xs font-semibold text-white">
                      {conversation.unread_count}
                    </span>
                  ) : null}
                  <span className="mt-1 block truncate text-xs text-muted">
                    {conversation.last_message?.body ?? "No messages yet"}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <div className="flex min-h-[620px] flex-col rounded-md border border-line bg-white">
          {!selectedConversationId ? (
            <div className="grid flex-1 place-items-center p-6 text-center">
              <p className="text-sm text-muted">No conversation selected.</p>
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between border-b border-line px-4 py-3">
                <div>
                  <h2 className="font-semibold">
                    {conversationLabel(selectedConversation)}
                  </h2>
                  {socketError ? (
                    <p role="alert" className="text-sm text-accent">
                      Message was not accepted.
                    </p>
                  ) : null}
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface"
                    onClick={() =>
                      void queryClient.invalidateQueries({
                        queryKey: chatMessagesQueryKey(selectedConversationId),
                      })
                    }
                  >
                    <RefreshCcw aria-hidden="true" className="h-4 w-4" />
                    Refresh
                  </button>
                  <button
                    type="button"
                    className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={clearConversation.isPending}
                    onClick={() => void clearConversation.mutateAsync()}
                  >
                    <Eraser aria-hidden="true" className="h-4 w-4" />
                    Clear
                  </button>
                </div>
              </div>

              <div className="flex-1 space-y-3 overflow-y-auto p-4">
                {messages.isLoading ? (
                  <p className="text-sm text-muted">Loading messages.</p>
                ) : messages.isError ? (
                  <p role="alert" className="text-sm text-accent">
                    {getErrorMessage(messages.error)}
                  </p>
                ) : messages.data?.items.length ? (
                  messages.data.items.map((message) => (
                    <article
                      key={message.id}
                      className={`max-w-[78%] rounded-md border border-line px-3 py-2 ${
                        message.sender_id === user?.id
                          ? "ml-auto bg-green-50"
                          : "bg-surface"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm">
                        {message.body}
                      </p>
                      <p className="mt-1 text-xs text-muted">
                        {formatChatTime(message.created_at)}
                      </p>
                    </article>
                  ))
                ) : (
                  <p className="text-sm text-muted">No messages yet.</p>
                )}
              </div>

              <form
                className="flex gap-2 border-t border-line p-4"
                onSubmit={handleSubmit}
              >
                <input
                  value={composer}
                  maxLength={4000}
                  onChange={(event) => setComposer(event.target.value)}
                  className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 text-sm"
                  placeholder="Write a message"
                />
                <button
                  type="submit"
                  disabled={!composer.trim() || sendRest.isPending}
                  className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Send aria-hidden="true" className="h-4 w-4" />
                  Send
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

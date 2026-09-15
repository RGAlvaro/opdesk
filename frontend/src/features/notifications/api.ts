// React Query hooks for the authenticated in-app notification inbox.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";

import { apiRequest } from "../../shared/api";
import {
  Notification,
  NotificationListResponse,
  NotificationRealtimeEvent,
  NotificationUnreadCountResponse,
} from "./types";

export const notificationsQueryKey = ["notifications"] as const;
export const unreadNotificationsQueryKey = [
  "notifications",
  "unread-count",
] as const;
const notificationsStaleTimeMs = 15_000;
const notificationsFallbackPollMs = 30_000;
const notificationReconnectMs = 5_000;

/** Fetch notifications for the current authenticated user. */
export function listNotifications(unread?: boolean) {
  const params = new URLSearchParams();
  if (unread !== undefined) {
    params.set("unread", String(unread));
  }
  const query = params.toString();
  return apiRequest<NotificationListResponse>(
    `/api/v1/notifications${query ? `?${query}` : ""}`,
  );
}

/** Fetch the current authenticated user's unread count. */
export function getUnreadNotificationCount() {
  return apiRequest<NotificationUnreadCountResponse>(
    "/api/v1/notifications/unread-count",
  );
}

/** Derive the notification WebSocket URL from the current browser origin. */
function notificationSocketUrl() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${window.location.host}/api/v1/notifications/ws`;
}

/** Insert a notification at the top of an existing paginated cache page once. */
function addNotificationToPage(
  current: NotificationListResponse | undefined,
  notification: Notification,
) {
  if (!current) {
    return current;
  }
  if (current.items.some((item) => item.id === notification.id)) {
    return current;
  }
  return {
    ...current,
    items: [notification, ...current.items],
    total: current.total + 1,
  };
}

/** Replace a cached notification when a read-state event arrives. */
function updateNotificationInPage(
  current: NotificationListResponse | undefined,
  notification: Notification,
) {
  if (!current) {
    return current;
  }
  return {
    ...current,
    items: current.items.map((item) =>
      item.id === notification.id ? notification : item,
    ),
  };
}

/** Mark every cached notification read after the bulk-read event arrives. */
function markCachedNotificationsRead(
  current: NotificationListResponse | undefined,
) {
  if (!current) {
    return current;
  }
  const readAt = new Date().toISOString();
  return {
    ...current,
    items: current.items.map((item) => ({
      ...item,
      read_at: item.read_at ?? readAt,
    })),
  };
}

/** Connect authenticated sessions to notification push events with REST recovery. */
export function useNotificationRealtime(enabled = true) {
  const queryClient = useQueryClient();
  const reconnectTimerRef = useRef<number | undefined>(undefined);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled || typeof WebSocket === "undefined") {
      return;
    }
    let disposed = false;

    /** Open or reopen the best-effort notification socket. */
    function connect() {
      if (disposed) {
        return;
      }
      const socket = new WebSocket(notificationSocketUrl());
      socketRef.current = socket;

      socket.addEventListener("message", (event) => {
        void handleRealtimeMessage(event);
      });

      socket.addEventListener("close", () => {
        if (disposed) {
          return;
        }
        void queryClient.invalidateQueries({ queryKey: notificationsQueryKey });
        void queryClient.invalidateQueries({
          queryKey: unreadNotificationsQueryKey,
        });
        reconnectTimerRef.current = window.setTimeout(
          connect,
          notificationReconnectMs,
        );
      });
    }

    /** Apply one server event after cancelling stale REST requests. */
    function handleRealtimeMessage(event: MessageEvent) {
      void queryClient.cancelQueries({ queryKey: unreadNotificationsQueryKey });
      void queryClient.cancelQueries({ queryKey: notificationsQueryKey });
      const data = JSON.parse(String(event.data)) as NotificationRealtimeEvent;
      queryClient.setQueryData<NotificationUnreadCountResponse>(
        unreadNotificationsQueryKey,
        { unread_count: data.unread_count },
      );
      if (data.type === "notification.created") {
        queryClient.setQueryData<NotificationListResponse>(
          notificationsQueryKey,
          (current) => addNotificationToPage(current, data.notification),
        );
        void queryClient.invalidateQueries({ queryKey: notificationsQueryKey });
      }
      if (data.type === "notification.read") {
        queryClient.setQueriesData<NotificationListResponse>(
          { queryKey: notificationsQueryKey },
          (current) => updateNotificationInPage(current, data.notification),
        );
      }
      if (data.type === "notifications.mark_all_read") {
        queryClient.setQueriesData<NotificationListResponse>(
          { queryKey: notificationsQueryKey },
          markCachedNotificationsRead,
        );
      }
    }

    connect();
    return () => {
      disposed = true;
      if (reconnectTimerRef.current !== undefined) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [enabled, queryClient]);
}

/** Keep the notification inbox in React Query cache. */
export function useNotifications(unread?: boolean) {
  return useQuery({
    queryKey:
      unread === undefined
        ? notificationsQueryKey
        : [...notificationsQueryKey, unread],
    queryFn: () => listNotifications(unread),
    staleTime: notificationsStaleTimeMs,
  });
}

/** Keep the app-shell unread notification count fresh. */
export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: unreadNotificationsQueryKey,
    queryFn: getUnreadNotificationCount,
    staleTime: notificationsStaleTimeMs,
    refetchInterval: notificationsFallbackPollMs,
  });
}

/** Change one notification's read state and refresh inbox count state. */
export function useSetNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { notificationId: string; read: boolean }) =>
      apiRequest<Notification>(
        `/api/v1/notifications/${payload.notificationId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ read: payload.read }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsQueryKey });
      queryClient.invalidateQueries({ queryKey: unreadNotificationsQueryKey });
    },
  });
}

/** Mark all current-user notifications read and refresh inbox count state. */
export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<undefined>("/api/v1/notifications/mark-all-read", {
        method: "POST",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: notificationsQueryKey });
      queryClient.invalidateQueries({ queryKey: unreadNotificationsQueryKey });
    },
  });
}

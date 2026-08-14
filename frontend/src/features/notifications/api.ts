// React Query hooks for the authenticated in-app notification inbox.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import {
  Notification,
  NotificationListResponse,
  NotificationUnreadCountResponse,
} from "./types";

export const notificationsQueryKey = ["notifications"] as const;
export const unreadNotificationsQueryKey = [
  "notifications",
  "unread-count",
] as const;
const notificationsStaleTimeMs = 15_000;

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

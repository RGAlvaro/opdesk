// Authenticated notification inbox for user-facing project and invitation events.

import { Bell, CheckCheck, Circle, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

import { getErrorMessage } from "../../shared/api";
import {
  useMarkAllNotificationsRead,
  useNotifications,
  useSetNotificationRead,
} from "./api";
import { Notification } from "./types";

/** Render relative time in compact recruiter-readable copy. */
function notificationTime(value: string) {
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

/** Render one inbox row with read-state and action controls. */
function NotificationRow({
  notification,
  onReadToggle,
  isUpdating,
}: {
  notification: Notification;
  onReadToggle: (notification: Notification) => void;
  isUpdating: boolean;
}) {
  const isUnread = notification.read_at === null;
  return (
    <li className="border-b border-line px-4 py-4 last:border-b-0">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <div className="flex items-center gap-2">
            {isUnread ? (
              <Circle
                aria-label="Unread"
                className="h-3 w-3 fill-brand text-brand"
              />
            ) : (
              <Circle aria-label="Read" className="h-3 w-3 text-muted" />
            )}
            <h2 className="text-sm font-semibold text-ink">
              {notification.title}
            </h2>
          </div>
          {notification.body ? (
            <p className="text-sm text-muted">{notification.body}</p>
          ) : null}
          <p className="text-xs text-muted">
            {notificationTime(notification.created_at)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {notification.action_url ? (
            <Link
              to={notification.action_url}
              className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface"
            >
              <ExternalLink aria-hidden="true" className="h-4 w-4" />
              Open
            </Link>
          ) : null}
          <button
            type="button"
            className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isUpdating}
            onClick={() => onReadToggle(notification)}
          >
            <CheckCheck aria-hidden="true" className="h-4 w-4" />
            {isUnread ? "Mark read" : "Mark unread"}
          </button>
        </div>
      </div>
    </li>
  );
}

/** Show the current user's persistent in-app notification inbox. */
export function NotificationsPage() {
  const notifications = useNotifications();
  const setRead = useSetNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();
  const unreadCount =
    notifications.data?.items.filter(
      (notification) => notification.read_at === null,
    ).length ?? 0;

  /** Toggle one notification read state from the row action. */
  function handleReadToggle(notification: Notification) {
    setRead.mutate({
      notificationId: notification.id,
      read: notification.read_at === null,
    });
  }

  return (
    <section className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Notifications</h1>
          <p className="text-sm text-muted">
            {unreadCount > 0
              ? `${unreadCount} unread notification${unreadCount === 1 ? "" : "s"}`
              : "All caught up"}
          </p>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
          disabled={markAllRead.isPending || unreadCount === 0}
          onClick={() => markAllRead.mutate()}
        >
          <CheckCheck aria-hidden="true" className="h-4 w-4" />
          Mark all read
        </button>
      </div>

      {notifications.isLoading ? (
        <div className="rounded-md border border-line bg-white p-4 text-sm text-muted">
          Loading notifications.
        </div>
      ) : null}

      {notifications.isError ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {getErrorMessage(notifications.error)}
        </div>
      ) : null}

      {setRead.isError ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {getErrorMessage(setRead.error)}
        </div>
      ) : null}

      {markAllRead.isError ? (
        <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {getErrorMessage(markAllRead.error)}
        </div>
      ) : null}

      {notifications.data && notifications.data.items.length === 0 ? (
        <div className="rounded-md border border-line bg-white p-8 text-center">
          <Bell aria-hidden="true" className="mx-auto h-8 w-8 text-brand" />
          <p className="mt-3 text-sm font-medium">No notifications yet</p>
        </div>
      ) : null}

      {notifications.data && notifications.data.items.length > 0 ? (
        <ul className="overflow-hidden rounded-md border border-line bg-white">
          {notifications.data.items.map((notification) => (
            <NotificationRow
              key={notification.id}
              notification={notification}
              onReadToggle={handleReadToggle}
              isUpdating={setRead.isPending}
            />
          ))}
        </ul>
      ) : null}
    </section>
  );
}

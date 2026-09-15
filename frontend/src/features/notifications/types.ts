// TypeScript contracts for the persistent in-app notifications feature.

export type NotificationType =
  | "invitation.organization"
  | "invitation.project"
  | "project.membership"
  | "project.updated"
  | "task.assigned"
  | "task.created"
  | "task.status_changed"
  | "ticket.comment"
  | "ticket.assignment_requested"
  | "chat.unread";

export type Notification = {
  id: string;
  recipient_user_id: string;
  type: NotificationType;
  title: string;
  body: string | null;
  action_url: string | null;
  resource_type: string | null;
  resource_id: string | null;
  read_at: string | null;
  created_at: string;
};

export type NotificationListResponse = {
  items: Notification[];
  total: number;
  limit: number;
  offset: number;
};

export type NotificationUnreadCountResponse = {
  unread_count: number;
};

export type NotificationRealtimeEvent =
  | {
      type: "notification.created" | "notification.read";
      notification: Notification;
      unread_count: number;
    }
  | {
      type: "notifications.mark_all_read";
      unread_count: number;
    };

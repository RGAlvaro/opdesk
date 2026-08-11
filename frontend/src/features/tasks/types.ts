// TypeScript contracts for task API responses, filters, and payloads.

import { PaginatedResponse } from "../organizations/types";

export type TaskStatus =
  | "todo"
  | "in_progress"
  | "blocked"
  | "done"
  | "cancelled";

export type TaskPriority = "low" | "medium" | "high" | "urgent";
export type TaskType = "internal" | "operational";

/** Task fields returned by the backend for organization members. */
export type Task = {
  id: string;
  organization_id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id: string | null;
  due_date: string | null;
  completed_at: string | null;
  estimated_hours: string | null;
  actual_hours: string | null;
  sort_order: number | null;
  blocked_reason: string | null;
  external_reference: string | null;
  task_type: TaskType;
  watcher_ids: string[];
  created_by_id: string;
  created_at: string;
  updated_at: string;
};

export type TaskListResponse = PaginatedResponse<Task>;

/** URL-backed task filters supported by the backend list endpoint. */
export type TaskFilters = {
  status?: TaskStatus;
  assignee_id?: string;
  priority?: TaskPriority;
  due_before?: string;
  due_after?: string;
  task_type?: TaskType;
  watcher_id?: string;
  external_reference?: string;
};

/** Payload accepted by task create and update mutations. */
export type TaskPayload = {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee_id?: string | null;
  due_date?: string | null;
  estimated_hours?: string | null;
  actual_hours?: string | null;
  sort_order?: number | null;
  blocked_reason?: string | null;
  external_reference?: string | null;
  task_type?: TaskType;
  watcher_ids?: string[];
};

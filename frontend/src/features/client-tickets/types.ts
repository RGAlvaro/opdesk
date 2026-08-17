// TypeScript contracts for restricted client ticket surfaces.

import { PaginatedResponse } from "../organizations/types";
import { Project } from "../projects/types";
import { TaskPriority, TaskStatus, TaskType } from "../tasks/types";
import { User } from "../auth/types";

/** Project client access row with safe account details. */
export type ProjectClientAccess = {
  id: string;
  organization_id: string;
  project_id: string;
  client_user_id: string;
  granted_by_id: string;
  revoked_at: string | null;
  client: User;
  created_at: string;
};

export type ProjectClientListResponse = PaginatedResponse<ProjectClientAccess>;

/** Ticket task shape used by internal and client ticket pages. */
export type Ticket = {
  id: string;
  organization_id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  assignee_id: string | null;
  client_user_id: string | null;
  task_type: TaskType;
  created_at: string;
  updated_at: string;
};

export type TicketListResponse = PaginatedResponse<Ticket>;

/** One persisted ticket feedback message. */
export type TicketComment = {
  id: string;
  task_id: string;
  organization_id: string;
  project_id: string;
  author_user_id: string;
  body: string;
  created_at: string;
  updated_at: string;
};

export type TicketCommentListResponse = PaginatedResponse<TicketComment>;

/** Pending ticket reassignment request visible to the target worker. */
export type TicketAssignmentRequest = {
  id: string;
  task_id: string;
  organization_id: string;
  project_id: string;
  requested_by_id: string;
  target_user_id: string;
  status: "pending" | "accepted" | "declined";
  ticket: Ticket;
  created_at: string;
  responded_at: string | null;
};

export type TicketAssignmentRequestListResponse =
  PaginatedResponse<TicketAssignmentRequest>;

export type ClientProjectListResponse = {
  items: Project[];
};

export type ProjectClientPayload = {
  email: string;
  full_name: string;
  password?: string | null;
};

export type TicketPayload = {
  subject: string;
  description: string;
  priority?: TaskPriority;
};

export type TicketUpdatePayload = {
  status?: TaskStatus;
  priority?: TaskPriority;
  assignee_id?: string | null;
};

export type TicketAssignmentRequestPayload = {
  target_user_id: string;
};

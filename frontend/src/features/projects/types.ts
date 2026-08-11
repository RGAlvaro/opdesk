// TypeScript contracts for project API responses and form payloads.

import { PaginatedResponse } from "../organizations/types";

export type ProjectStatus =
  | "planned"
  | "active"
  | "on_hold"
  | "completed"
  | "cancelled";

export type ProjectVisibility = "organization" | "project_members";

/** Project fields returned by the backend for organization members. */
export type Project = {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  is_archived: boolean;
  status: ProjectStatus;
  start_date: string | null;
  end_date: string | null;
  budget_amount: string | null;
  budget_currency: string | null;
  visibility: ProjectVisibility;
  project_owner_id: string | null;
  created_at: string;
  updated_at: string;
};

export type ProjectListResponse = PaginatedResponse<Project>;

/** Payload accepted by project create and update mutations. */
export type ProjectPayload = {
  name?: string;
  description?: string | null;
  is_archived?: boolean;
  status?: ProjectStatus;
  start_date?: string | null;
  end_date?: string | null;
  budget_amount?: string | null;
  budget_currency?: string | null;
  visibility?: ProjectVisibility;
  project_owner_id?: string | null;
};

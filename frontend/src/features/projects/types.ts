// TypeScript contracts for project API responses and form payloads.

import { PaginatedResponse } from "../organizations/types";

/** Project fields returned by the backend for organization members. */
export type Project = {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type ProjectListResponse = PaginatedResponse<Project>;

/** Payload accepted by project create and update mutations. */
export type ProjectPayload = {
  name?: string;
  description?: string | null;
  is_archived?: boolean;
};

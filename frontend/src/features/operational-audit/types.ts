// TypeScript contracts for owner/admin operational audit responses.

import { PaginatedResponse } from "../organizations/types";

export type OperationalAuditStatus =
  | "started"
  | "succeeded"
  | "failed"
  | "skipped";

/** Safe scheduled-job audit row returned by the admin API. */
export type OperationalAuditRun = {
  id: string;
  job_name: string;
  scheduled_for: string | null;
  started_at: string;
  finished_at: string | null;
  status: OperationalAuditStatus;
  records_seen: number | null;
  records_changed: number | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type OperationalAuditListResponse =
  PaginatedResponse<OperationalAuditRun>;

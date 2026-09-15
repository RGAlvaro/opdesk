// React Query hooks for owner/admin operational audit rows.

import { useQuery } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import { OperationalAuditListResponse, OperationalAuditStatus } from "./types";

export const operationalAuditQueryKey = ["operational-audit"] as const;
const operationalAuditStaleTimeMs = 30_000;

export type OperationalAuditFilters = {
  jobName?: string;
  status?: OperationalAuditStatus | "";
  limit?: number;
  offset?: number;
};

/** Fetch owner/admin-visible scheduled-job audit rows. */
export function listOperationalAudit(filters: OperationalAuditFilters = {}) {
  const params = new URLSearchParams();
  params.set("limit", String(filters.limit ?? 20));
  params.set("offset", String(filters.offset ?? 0));
  if (filters.jobName) {
    params.set("job_name", filters.jobName);
  }
  if (filters.status) {
    params.set("status", filters.status);
  }
  return apiRequest<OperationalAuditListResponse>(
    `/api/v1/admin/operational-audit?${params.toString()}`,
  );
}

/** Keep operational audit rows in query cache for the admin screen. */
export function useOperationalAudit(filters: OperationalAuditFilters) {
  return useQuery({
    queryKey: [
      ...operationalAuditQueryKey,
      filters.jobName ?? "",
      filters.status ?? "",
      filters.limit ?? 20,
      filters.offset ?? 0,
    ],
    queryFn: () => listOperationalAudit(filters),
    staleTime: operationalAuditStaleTimeMs,
  });
}

// Owner/admin screen for inspecting scheduled-job operational audit rows.

import { Activity, AlertTriangle, Filter } from "lucide-react";
import { FormEvent, useState } from "react";

import { getErrorMessage } from "../../shared/api";
import { useOperationalAudit } from "./api";
import { OperationalAuditRun, OperationalAuditStatus } from "./types";

const statuses: Array<OperationalAuditStatus | ""> = [
  "",
  "started",
  "succeeded",
  "failed",
  "skipped",
];

/** Format timestamps in the same compact style as other OpsDesk lists. */
function formatAuditTime(value: string | null) {
  if (!value) {
    return "Not finished";
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

/** Render one audit run row with safe operational details only. */
function AuditRow({ run }: { run: OperationalAuditRun }) {
  return (
    <tr className="border-b border-line last:border-b-0">
      <td className="px-4 py-3 align-top text-sm font-medium text-ink">
        {run.job_name}
      </td>
      <td className="px-4 py-3 align-top text-sm">
        <span
          className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
            run.status === "failed"
              ? "bg-red-50 text-red-700"
              : run.status === "succeeded"
                ? "bg-green-50 text-green-700"
                : "bg-surface text-muted"
          }`}
        >
          {run.status}
        </span>
      </td>
      <td className="px-4 py-3 align-top text-sm text-muted">
        {formatAuditTime(run.started_at)}
      </td>
      <td className="px-4 py-3 align-top text-sm text-muted">
        {formatAuditTime(run.finished_at)}
      </td>
      <td className="px-4 py-3 align-top text-sm text-muted">
        {run.records_seen ?? "-"} / {run.records_changed ?? "-"}
      </td>
      <td className="px-4 py-3 align-top text-sm text-muted">
        {run.error_code ? (
          <span>
            {run.error_code}
            {run.error_message ? `: ${run.error_message}` : ""}
          </span>
        ) : (
          "-"
        )}
      </td>
    </tr>
  );
}

/** Show scheduled-job audit rows with owner/admin filters and safe details. */
export function OperationalAuditPage() {
  const [draftJobName, setDraftJobName] = useState("");
  const [draftStatus, setDraftStatus] = useState<OperationalAuditStatus | "">(
    "",
  );
  const [filters, setFilters] = useState<{
    jobName?: string;
    status?: OperationalAuditStatus | "";
  }>({});
  const audit = useOperationalAudit({
    jobName: filters.jobName,
    status: filters.status,
  });

  /** Apply filters without writing empty values into the query key. */
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFilters({
      jobName: draftJobName.trim() || undefined,
      status: draftStatus,
    });
  }

  return (
    <section className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Operational audit</h1>
        <p className="text-sm text-muted">
          Scheduled job runs, safe counts, and sanitized failure details.
        </p>
      </div>

      <form
        className="grid gap-3 rounded-md border border-line bg-white p-4 sm:grid-cols-[1fr_180px_auto]"
        onSubmit={handleSubmit}
      >
        <label className="space-y-1 text-sm">
          <span className="font-medium">Job name</span>
          <input
            className="w-full rounded-md border border-line px-3 py-2"
            value={draftJobName}
            onChange={(event) => setDraftJobName(event.target.value)}
            placeholder="external_delivery_retry_sweep"
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">Status</span>
          <select
            className="w-full rounded-md border border-line px-3 py-2"
            value={draftStatus}
            onChange={(event) =>
              setDraftStatus(event.target.value as OperationalAuditStatus | "")
            }
          >
            {statuses.map((status) => (
              <option key={status || "all"} value={status}>
                {status || "all"}
              </option>
            ))}
          </select>
        </label>
        <button
          type="submit"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-medium text-white hover:bg-brand-dark"
        >
          <Filter aria-hidden="true" className="h-4 w-4" />
          Filter
        </button>
      </form>

      {audit.isLoading ? (
        <div className="rounded-md border border-line bg-white p-4 text-sm text-muted">
          Loading operational audit.
        </div>
      ) : null}

      {audit.isError ? (
        <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          <AlertTriangle aria-hidden="true" className="h-4 w-4" />
          {getErrorMessage(audit.error)}
        </div>
      ) : null}

      {audit.data && audit.data.items.length === 0 ? (
        <div className="rounded-md border border-line bg-white p-8 text-center">
          <Activity aria-hidden="true" className="mx-auto h-8 w-8 text-brand" />
          <p className="mt-3 text-sm font-medium">No audit rows found</p>
        </div>
      ) : null}

      {audit.data && audit.data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-md border border-line bg-white">
          <table className="min-w-full border-collapse">
            <thead className="bg-surface text-left text-xs uppercase text-muted">
              <tr>
                <th className="px-4 py-3 font-semibold">Job</th>
                <th className="px-4 py-3 font-semibold">Status</th>
                <th className="px-4 py-3 font-semibold">Started</th>
                <th className="px-4 py-3 font-semibold">Finished</th>
                <th className="px-4 py-3 font-semibold">Seen / changed</th>
                <th className="px-4 py-3 font-semibold">Error</th>
              </tr>
            </thead>
            <tbody>
              {audit.data.items.map((run) => (
                <AuditRow key={run.id} run={run} />
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

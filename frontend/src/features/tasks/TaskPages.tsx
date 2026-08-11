// Route pages for task list, creation, detail, and updates.

import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, CheckCircle2, Plus, Save, Tag } from "lucide-react";
import { useCallback, useEffect, useMemo } from "react";
import { useForm } from "react-hook-form";
import { useQueryClient } from "@tanstack/react-query";
import {
  Link,
  Navigate,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { z } from "zod";

import { ApiError, getErrorMessage } from "../../shared/api";
import { sessionQueryKey } from "../auth/session";
import { useSession } from "../auth/session";
import { useOrganization, useOrganizationMembers } from "../organizations/api";
import {
  OrganizationMembership,
  OrganizationRole,
  PaginatedResponse,
  PaginationParams,
} from "../organizations/types";
import { ProjectHeader } from "../projects/ProjectPages";
import { useProject } from "../projects/api";
import {
  useApplyTaskLabel,
  useCreateTask,
  useProjectLabels,
  useProjectTasks,
  useRemoveTaskLabel,
  useTask,
  useUpdateTask,
} from "./api";
import {
  TaskFilters,
  TaskLabel,
  TaskPriority,
  TaskStatus,
  TaskType,
} from "./types";

const taskStatuses = [
  "todo",
  "in_progress",
  "blocked",
  "done",
  "cancelled",
] as const satisfies readonly TaskStatus[];

const taskPriorities = [
  "low",
  "medium",
  "high",
  "urgent",
] as const satisfies readonly TaskPriority[];

const taskTypes = [
  "internal",
  "operational",
] as const satisfies readonly TaskType[];

const taskSchema = z.object({
  title: z.string().trim().min(1, "Task title is required.").max(200),
  description: z.string().trim().optional(),
  status: z.enum(taskStatuses).optional(),
  priority: z.enum(taskPriorities),
  assignee_id: z.string().trim().optional(),
  due_date: z.string().trim().optional(),
  estimated_hours: z.string().trim().optional(),
  actual_hours: z.string().trim().optional(),
  sort_order: z.string().trim().optional(),
  blocked_reason: z.string().trim().max(1000).optional(),
  external_reference: z.string().trim().max(200).optional(),
  task_type: z.enum(taskTypes),
  watcher_ids: z.array(z.string()).optional(),
});

type TaskFormValues = z.infer<typeof taskSchema>;
const defaultPageLimit = 20;

/** Read standard pagination values from route query parameters. */
function paginationFromSearch(searchParams: URLSearchParams): PaginationParams {
  const limit = Number(searchParams.get("limit") ?? defaultPageLimit);
  const offset = Number(searchParams.get("offset") ?? 0);
  return {
    limit:
      Number.isInteger(limit) && limit > 0 && limit <= 100
        ? limit
        : defaultPageLimit,
    offset: Number.isInteger(offset) && offset >= 0 ? offset : 0,
  };
}

/** Render previous/next controls for paginated backend lists. */
function PaginationControls<TItem>({
  page,
  onPageChange,
}: {
  page: PaginatedResponse<TItem>;
  onPageChange: (pagination: PaginationParams) => void;
}) {
  const previousOffset = Math.max(0, page.offset - page.limit);
  const nextOffset = page.offset + page.limit;
  const canGoPrevious = page.offset > 0;
  const canGoNext = nextOffset < page.total;

  return (
    <div className="flex flex-col gap-3 rounded-md border border-line bg-white p-4 text-sm sm:flex-row sm:items-center sm:justify-between">
      <p className="text-muted">
        Showing {page.total === 0 ? 0 : page.offset + 1}-
        {Math.min(page.offset + page.items.length, page.total)} of {page.total}
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          disabled={!canGoPrevious}
          className="rounded-md border border-line px-3 py-2 font-medium hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
          onClick={() =>
            onPageChange({ limit: page.limit, offset: previousOffset })
          }
        >
          Previous
        </button>
        <button
          type="button"
          disabled={!canGoNext}
          className="rounded-md border border-line px-3 py-2 font-medium hover:bg-surface disabled:cursor-not-allowed disabled:opacity-60"
          onClick={() =>
            onPageChange({ limit: page.limit, offset: nextOffset })
          }
        >
          Next
        </button>
      </div>
    </div>
  );
}

/** Render backend and network errors using safe user-facing copy. */
function ErrorNotice({ error }: { error: unknown }) {
  return (
    <p
      role="alert"
      className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
    >
      {getErrorMessage(error)}
    </p>
  );
}

/** Identify auth-loss responses from task API calls. */
function isAuthLoss(error: unknown) {
  return error instanceof ApiError && error.status === 401;
}

/** Clear cached session state and send the user back to login. */
function useFeatureAuthLoss() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  /** Keep task 401 handling consistent across queries and mutations. */
  const handleAuthLoss = useCallback(
    async (error: unknown) => {
      if (!isAuthLoss(error)) {
        return false;
      }
      await queryClient.cancelQueries({ queryKey: sessionQueryKey });
      queryClient.removeQueries({ queryKey: sessionQueryKey });
      navigate("/login", { replace: true });
      return true;
    },
    [navigate, queryClient],
  );

  return handleAuthLoss;
}

/** Redirect to login whenever a task query reports auth loss. */
function AuthErrorRedirect({ error }: { error: unknown }) {
  const handleAuthLoss = useFeatureAuthLoss();

  useEffect(() => {
    void handleAuthLoss(error);
  }, [error, handleAuthLoss]);

  return null;
}

/** Format backend timestamps without changing their business meaning. */
function formatDateTime(value: string | undefined | null) {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

/** Format backend dates for compact task surfaces. */
function formatDate(value: string | undefined | null) {
  if (!value) {
    return "Not set";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
  }).format(new Date(`${value}T00:00:00`));
}

/** Convert enum-like values into short readable labels. */
function optionLabel(value: string | null | undefined) {
  if (!value) {
    return "Not set";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/** Return true when the actor can manage any task in the organization. */
function canManageAllTasks(role: OrganizationRole | undefined) {
  return role === "owner" || role === "admin";
}

/** Build URL-backed task filters from the current search string. */
function filtersFromSearch(searchParams: URLSearchParams): TaskFilters {
  const status = searchParams.get("status");
  const priority = searchParams.get("priority");
  const taskType = searchParams.get("task_type");
  return {
    ...(taskStatuses.includes(status as TaskStatus)
      ? { status: status as TaskStatus }
      : {}),
    ...(taskPriorities.includes(priority as TaskPriority)
      ? { priority: priority as TaskPriority }
      : {}),
    ...(searchParams.get("assignee_id")
      ? { assignee_id: searchParams.get("assignee_id") ?? undefined }
      : {}),
    ...(searchParams.get("due_before")
      ? { due_before: searchParams.get("due_before") ?? undefined }
      : {}),
    ...(searchParams.get("due_after")
      ? { due_after: searchParams.get("due_after") ?? undefined }
      : {}),
    ...(taskTypes.includes(taskType as TaskType)
      ? { task_type: taskType as TaskType }
      : {}),
    ...(searchParams.get("watcher_id")
      ? { watcher_id: searchParams.get("watcher_id") ?? undefined }
      : {}),
    ...(searchParams.get("external_reference")
      ? {
          external_reference:
            searchParams.get("external_reference") ?? undefined,
        }
      : {}),
    ...(searchParams.get("label_id")
      ? { label_id: searchParams.get("label_id") ?? undefined }
      : {}),
  };
}

/** Build the payload accepted by create and update task endpoints. */
function taskPayload(values: TaskFormValues, includeStatus: boolean) {
  const description = values.description?.trim();
  const assigneeId = values.assignee_id?.trim();
  const dueDate = values.due_date?.trim();
  const estimatedHours = values.estimated_hours?.trim();
  const actualHours = values.actual_hours?.trim();
  const sortOrder = values.sort_order?.trim();
  const blockedReason = values.blocked_reason?.trim();
  const externalReference = values.external_reference?.trim();
  return {
    title: values.title.trim(),
    description: description ? description : null,
    priority: values.priority,
    ...(includeStatus && values.status ? { status: values.status } : {}),
    assignee_id: assigneeId ? assigneeId : null,
    due_date: dueDate ? dueDate : null,
    estimated_hours: estimatedHours ? estimatedHours : null,
    actual_hours: actualHours ? actualHours : null,
    sort_order: sortOrder ? Number(sortOrder) : null,
    blocked_reason: blockedReason ? blockedReason : null,
    external_reference: externalReference ? externalReference : null,
    task_type: values.task_type,
    watcher_ids: values.watcher_ids ?? [],
  };
}

/** Resolve an assignee label from member data when it is available. */
function assigneeLabel(
  assigneeId: string | null,
  members: OrganizationMembership[] | undefined,
) {
  if (!assigneeId) {
    return "Unassigned";
  }
  const membership = members?.find((member) => member.user_id === assigneeId);
  return membership
    ? `${membership.user.full_name} (${membership.user.email})`
    : assigneeId;
}

/** Render task label chips with archived labels visually subdued. */
function TaskLabelChips({ labels }: { labels: TaskLabel[] }) {
  if (labels.length === 0) {
    return <span className="text-xs text-muted">No labels</span>;
  }
  return (
    <div className="flex max-w-md flex-wrap gap-1">
      {labels.map((label) => (
        <span
          key={label.id}
          className={`inline-flex items-center gap-1 rounded-md bg-white px-2 py-1 text-xs font-semibold ${
            label.archived_at ? "opacity-60" : ""
          }`}
        >
          <span
            aria-hidden="true"
            className="h-2.5 w-2.5 rounded-sm"
            style={{ backgroundColor: label.color }}
          />
          {label.name}
        </span>
      ))}
    </div>
  );
}

/** Link back to one project's task list with consistent styling. */
function BackToProjectTasks({ projectId }: { projectId: string | undefined }) {
  return (
    <Link
      to={projectId ? `/app/projects/${projectId}/tasks` : "/app/organizations"}
      className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
    >
      <ArrowLeft aria-hidden="true" className="h-4 w-4" />
      Tasks
    </Link>
  );
}

/** Show one project's task list with backend-backed filters. */
export function TaskListPage() {
  const { projectId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(
    () => filtersFromSearch(searchParams),
    [searchParams],
  );
  const pagination = paginationFromSearch(searchParams);
  const project = useProject(projectId);
  const organization = useOrganization(project.data?.organization_id);
  const members = useOrganizationMembers(
    project.data?.organization_id,
    canManageAllTasks(organization.data?.role),
  );
  const labels = useProjectLabels(projectId, true);
  const tasks = useProjectTasks(projectId, filters, pagination);

  /** Persist a filter value into the shareable route query string. */
  function setFilter(name: keyof TaskFilters, value: string) {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(name, value);
    } else {
      next.delete(name);
    }
    next.set("limit", String(pagination.limit));
    next.set("offset", "0");
    setSearchParams(next);
  }

  /** Persist task pagination in the route query string. */
  function setPagination(nextPagination: PaginationParams) {
    const next = new URLSearchParams(searchParams);
    next.set("limit", String(nextPagination.limit));
    next.set("offset", String(nextPagination.offset));
    setSearchParams(next);
  }

  if (project.isLoading || tasks.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading tasks.
      </p>
    );
  }

  if (project.isError || tasks.isError) {
    const error = project.error ?? tasks.error;
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={error} />
        <BackToProjectTasks projectId={projectId} />
        <h1 className="text-2xl font-semibold">Tasks not available</h1>
        <ErrorNotice error={error} />
      </section>
    );
  }

  if (!project.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  const items = tasks.data?.items ?? [];
  const canCreate = !project.data.is_archived;

  return (
    <section className="space-y-6">
      <Link
        to={`/app/projects/${project.data.id}`}
        className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        {project.data.name}
      </Link>
      <ProjectHeader project={project.data} />
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Tasks</h1>
          <p className="mt-2 text-muted">
            {tasks.data?.total ?? 0} total task
            {(tasks.data?.total ?? 0) === 1 ? "" : "s"}.
          </p>
        </div>
        {canCreate ? (
          <Link
            to={`/app/projects/${project.data.id}/tasks/new`}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
          >
            <Plus aria-hidden="true" className="h-4 w-4" />
            New task
          </Link>
        ) : (
          <span className="rounded-md bg-red-50 px-3 py-2 text-sm font-medium text-accent">
            Archived project
          </span>
        )}
      </div>

      <TaskFiltersPanel
        filters={filters}
        members={members.data?.items}
        labels={labels.data?.items}
        onFilterChange={setFilter}
      />

      {items.length === 0 ? (
        <div className="rounded-md border border-line bg-white p-6 shadow-panel">
          <h2 className="text-lg font-semibold">No tasks found</h2>
          <p className="mt-2 text-sm text-muted">
            {canCreate
              ? "Create a task or adjust filters."
              : "Archived projects do not accept new tasks."}
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-md border border-line bg-white">
            <table className="w-full min-w-[760px] border-separate border-spacing-y-2 p-3 text-left text-sm">
              <thead className="text-muted">
                <tr>
                  <th className="px-3 py-2 font-medium">Task</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Priority</th>
                  <th className="px-3 py-2 font-medium">Assignee</th>
                  <th className="px-3 py-2 font-medium">Labels</th>
                  <th className="px-3 py-2 font-medium">Due</th>
                  <th className="px-3 py-2 font-medium">Type</th>
                </tr>
              </thead>
              <tbody>
                {items.map((task) => (
                  <tr key={task.id} className="bg-surface">
                    <td className="rounded-l-md px-3 py-3">
                      <Link
                        to={`/app/tasks/${task.id}`}
                        className="break-words font-medium text-brand hover:underline"
                      >
                        {task.title}
                      </Link>
                      {task.completed_at ? (
                        <div className="mt-1 text-xs text-muted">
                          Completed {formatDateTime(task.completed_at)}
                        </div>
                      ) : null}
                    </td>
                    <td className="px-3 py-3">{optionLabel(task.status)}</td>
                    <td className="px-3 py-3">{optionLabel(task.priority)}</td>
                    <td className="px-3 py-3">
                      {assigneeLabel(task.assignee_id, members.data?.items)}
                    </td>
                    <td className="px-3 py-3">
                      <TaskLabelChips labels={task.labels} />
                    </td>
                    <td className="px-3 py-3">{formatDate(task.due_date)}</td>
                    <td className="rounded-r-md px-3 py-3">
                      {optionLabel(task.task_type)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {tasks.data ? (
            <PaginationControls
              page={tasks.data}
              onPageChange={setPagination}
            />
          ) : null}
        </>
      )}
    </section>
  );
}

/** Render URL-backed task filters without changing layout dimensions. */
function TaskFiltersPanel({
  filters,
  members,
  labels,
  onFilterChange,
}: {
  filters: TaskFilters;
  members: OrganizationMembership[] | undefined;
  labels: TaskLabel[] | undefined;
  onFilterChange: (name: keyof TaskFilters, value: string) => void;
}) {
  return (
    <div className="grid gap-3 rounded-md border border-line bg-white p-4 sm:grid-cols-2 lg:grid-cols-5">
      <div>
        <label htmlFor="filter_status" className="block text-sm font-medium">
          Status
        </label>
        <select
          id="filter_status"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          value={filters.status ?? ""}
          onChange={(event) => onFilterChange("status", event.target.value)}
        >
          <option value="">Any</option>
          {taskStatuses.map((status) => (
            <option key={status} value={status}>
              {optionLabel(status)}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="filter_priority" className="block text-sm font-medium">
          Priority
        </label>
        <select
          id="filter_priority"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          value={filters.priority ?? ""}
          onChange={(event) => onFilterChange("priority", event.target.value)}
        >
          <option value="">Any</option>
          {taskPriorities.map((priority) => (
            <option key={priority} value={priority}>
              {optionLabel(priority)}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="filter_assignee" className="block text-sm font-medium">
          Assignee
        </label>
        <select
          id="filter_assignee"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          value={filters.assignee_id ?? ""}
          onChange={(event) =>
            onFilterChange("assignee_id", event.target.value)
          }
        >
          <option value="">Any</option>
          {members?.map((member) => (
            <option key={member.user_id} value={member.user_id}>
              {member.user.full_name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="filter_due_after" className="block text-sm font-medium">
          Due after
        </label>
        <input
          id="filter_due_after"
          type="date"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          value={filters.due_after ?? ""}
          onChange={(event) => onFilterChange("due_after", event.target.value)}
        />
      </div>
      <div>
        <label
          htmlFor="filter_due_before"
          className="block text-sm font-medium"
        >
          Due before
        </label>
        <input
          id="filter_due_before"
          type="date"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          value={filters.due_before ?? ""}
          onChange={(event) => onFilterChange("due_before", event.target.value)}
        />
      </div>
      <div>
        <label htmlFor="filter_label" className="block text-sm font-medium">
          Label
        </label>
        <select
          id="filter_label"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          value={filters.label_id ?? ""}
          onChange={(event) => onFilterChange("label_id", event.target.value)}
        >
          <option value="">Any</option>
          {labels?.map((label) => (
            <option key={label.id} value={label.id}>
              {label.archived_at ? `${label.name} (archived)` : label.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="filter_task_type" className="block text-sm font-medium">
          Type
        </label>
        <select
          id="filter_task_type"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          value={filters.task_type ?? ""}
          onChange={(event) => onFilterChange("task_type", event.target.value)}
        >
          <option value="">Any</option>
          {taskTypes.map((taskType) => (
            <option key={taskType} value={taskType}>
              {optionLabel(taskType)}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="filter_watcher" className="block text-sm font-medium">
          Watcher
        </label>
        <select
          id="filter_watcher"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          value={filters.watcher_id ?? ""}
          onChange={(event) => onFilterChange("watcher_id", event.target.value)}
        >
          <option value="">Any</option>
          {members?.map((member) => (
            <option key={member.user_id} value={member.user_id}>
              {member.user.full_name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label
          htmlFor="filter_external_reference"
          className="block text-sm font-medium"
        >
          External reference
        </label>
        <input
          id="filter_external_reference"
          type="text"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          value={filters.external_reference ?? ""}
          onChange={(event) =>
            onFilterChange("external_reference", event.target.value)
          }
        />
      </div>
    </div>
  );
}

/** Render task creation form with role-aware assignee choices. */
export function TaskNewPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const handleAuthLoss = useFeatureAuthLoss();
  const { data: user } = useSession();
  const project = useProject(projectId);
  const organization = useOrganization(project.data?.organization_id);
  const canUseMemberList = canManageAllTasks(organization.data?.role);
  const members = useOrganizationMembers(
    project.data?.organization_id,
    canUseMemberList,
  );
  const createTask = useCreateTask(projectId ?? "");
  const form = useForm<TaskFormValues>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      title: "",
      description: "",
      priority: "medium",
      assignee_id: "",
      due_date: "",
      estimated_hours: "",
      actual_hours: "",
      sort_order: "",
      blocked_reason: "",
      external_reference: "",
      task_type: "internal",
      watcher_ids: [],
    },
  });

  /** Persist a new task without sending a client-owned default status. */
  async function onSubmit(values: TaskFormValues) {
    try {
      const task = await createTask.mutateAsync(taskPayload(values, false));
      navigate(`/app/tasks/${task.id}`);
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  if (project.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading project.
      </p>
    );
  }

  if (project.isError) {
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={project.error} />
        <BackToProjectTasks projectId={projectId} />
        <ErrorNotice error={project.error} />
      </section>
    );
  }

  if (!project.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  if (project.data.is_archived) {
    return (
      <section className="space-y-4">
        <BackToProjectTasks projectId={project.data.id} />
        <ProjectHeader project={project.data} />
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          Archived projects do not accept new tasks.
        </p>
      </section>
    );
  }

  return (
    <section className="max-w-2xl space-y-6">
      <BackToProjectTasks projectId={project.data.id} />
      <div className="rounded-md border border-line bg-white p-6 shadow-panel">
        <h1 className="text-2xl font-semibold">New task</h1>
        <TaskForm
          form={form}
          submitLabel="Create task"
          isPending={createTask.isPending}
          actorRole={organization.data?.role}
          userId={user?.id}
          members={canUseMemberList ? members.data?.items : undefined}
          includeStatus={false}
          onSubmit={onSubmit}
        />
        {createTask.isError ? (
          <div className="mt-4">
            <ErrorNotice error={createTask.error} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

/** Shared task form fields for create and update screens. */
function TaskForm({
  form,
  submitLabel,
  isPending,
  actorRole,
  userId,
  members,
  includeStatus,
  onSubmit,
}: {
  form: ReturnType<typeof useForm<TaskFormValues>>;
  submitLabel: string;
  isPending: boolean;
  actorRole: OrganizationRole | undefined;
  userId: string | undefined;
  members: OrganizationMembership[] | undefined;
  includeStatus: boolean;
  onSubmit: (values: TaskFormValues) => Promise<void>;
}) {
  const canAssignAny = canManageAllTasks(actorRole);

  return (
    <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="task_title" className="block text-sm font-medium">
          Title
        </label>
        <input
          id="task_title"
          type="text"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          {...form.register("title")}
        />
        {form.formState.errors.title ? (
          <p className="mt-1 text-sm text-accent">
            {form.formState.errors.title.message}
          </p>
        ) : null}
      </div>
      <div>
        <label htmlFor="task_description" className="block text-sm font-medium">
          Description
        </label>
        <textarea
          id="task_description"
          className="mt-1 min-h-28 w-full rounded-md border border-line px-3 py-2"
          {...form.register("description")}
        />
      </div>
      {includeStatus ? (
        <div>
          <label htmlFor="task_status" className="block text-sm font-medium">
            Status
          </label>
          <select
            id="task_status"
            className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
            {...form.register("status")}
          >
            {taskStatuses.map((status) => (
              <option key={status} value={status}>
                {optionLabel(status)}
              </option>
            ))}
          </select>
        </div>
      ) : null}
      <div>
        <label htmlFor="task_priority" className="block text-sm font-medium">
          Priority
        </label>
        <select
          id="task_priority"
          className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
          {...form.register("priority")}
        >
          {taskPriorities.map((priority) => (
            <option key={priority} value={priority}>
              {optionLabel(priority)}
            </option>
          ))}
        </select>
      </div>
      {canAssignAny || !includeStatus ? (
        <div>
          <label htmlFor="task_assignee" className="block text-sm font-medium">
            Assignee
          </label>
          <select
            id="task_assignee"
            className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
            {...form.register("assignee_id")}
          >
            <option value="">Unassigned</option>
            {canAssignAny ? (
              members?.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {member.user.full_name} ({member.user.email})
                </option>
              ))
            ) : userId ? (
              <option value={userId}>Me</option>
            ) : null}
          </select>
        </div>
      ) : null}
      <div>
        <label htmlFor="task_due_date" className="block text-sm font-medium">
          Due date
        </label>
        <input
          id="task_due_date"
          type="date"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          {...form.register("due_date")}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="task_type" className="block text-sm font-medium">
            Type
          </label>
          <select
            id="task_type"
            className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
            {...form.register("task_type")}
          >
            {taskTypes.map((taskType) => (
              <option key={taskType} value={taskType}>
                {optionLabel(taskType)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label
            htmlFor="task_sort_order"
            className="block text-sm font-medium"
          >
            Sort order
          </label>
          <input
            id="task_sort_order"
            type="number"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("sort_order")}
          />
        </div>
        <div>
          <label
            htmlFor="task_estimated_hours"
            className="block text-sm font-medium"
          >
            Estimated hours
          </label>
          <input
            id="task_estimated_hours"
            type="number"
            min="0"
            step="0.25"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("estimated_hours")}
          />
        </div>
        <div>
          <label
            htmlFor="task_actual_hours"
            className="block text-sm font-medium"
          >
            Actual hours
          </label>
          <input
            id="task_actual_hours"
            type="number"
            min="0"
            step="0.25"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("actual_hours")}
          />
        </div>
      </div>
      <div>
        <label
          htmlFor="task_external_reference"
          className="block text-sm font-medium"
        >
          External reference
        </label>
        <input
          id="task_external_reference"
          type="text"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          {...form.register("external_reference")}
        />
      </div>
      <div>
        <label
          htmlFor="task_blocked_reason"
          className="block text-sm font-medium"
        >
          Blocked reason
        </label>
        <textarea
          id="task_blocked_reason"
          className="mt-1 min-h-20 w-full rounded-md border border-line px-3 py-2"
          {...form.register("blocked_reason")}
        />
      </div>
      {canAssignAny ? (
        <div>
          <label htmlFor="task_watchers" className="block text-sm font-medium">
            Watchers
          </label>
          <select
            id="task_watchers"
            multiple
            className="mt-1 min-h-28 w-full rounded-md border border-line bg-white px-3 py-2"
            {...form.register("watcher_ids")}
          >
            {members?.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {member.user.full_name} ({member.user.email})
              </option>
            ))}
          </select>
        </div>
      ) : null}
      <button
        type="submit"
        disabled={isPending}
        className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
      >
        <Save aria-hidden="true" className="h-4 w-4" />
        {isPending ? "Saving" : submitLabel}
      </button>
    </form>
  );
}

/** Render task detail and role-aware update controls. */
export function TaskDetailPage() {
  const { taskId } = useParams();
  const handleAuthLoss = useFeatureAuthLoss();
  const { data: user } = useSession();
  const task = useTask(taskId);
  const project = useProject(task.data?.project_id);
  const organization = useOrganization(task.data?.organization_id);
  const canUseMemberList = canManageAllTasks(organization.data?.role);
  const members = useOrganizationMembers(
    task.data?.organization_id,
    canUseMemberList,
  );
  const labels = useProjectLabels(task.data?.project_id, true);
  const updateTask = useUpdateTask(taskId ?? "");
  const applyTaskLabel = useApplyTaskLabel(taskId ?? "", task.data?.project_id);
  const removeTaskLabel = useRemoveTaskLabel(
    taskId ?? "",
    task.data?.project_id,
  );
  const form = useForm<TaskFormValues>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      title: "",
      description: "",
      status: "todo",
      priority: "medium",
      assignee_id: "",
      due_date: "",
      estimated_hours: "",
      actual_hours: "",
      sort_order: "",
      blocked_reason: "",
      external_reference: "",
      task_type: "internal",
      watcher_ids: [],
    },
  });

  useEffect(() => {
    if (task.data) {
      form.reset({
        title: task.data.title,
        description: task.data.description ?? "",
        status: task.data.status,
        priority: task.data.priority,
        assignee_id: task.data.assignee_id ?? "",
        due_date: task.data.due_date ?? "",
        estimated_hours: task.data.estimated_hours ?? "",
        actual_hours: task.data.actual_hours ?? "",
        sort_order:
          task.data.sort_order === null ? "" : String(task.data.sort_order),
        blocked_reason: task.data.blocked_reason ?? "",
        external_reference: task.data.external_reference ?? "",
        task_type: task.data.task_type,
        watcher_ids: task.data.watcher_ids,
      });
    }
  }, [form, task.data]);

  const canEdit =
    canManageAllTasks(organization.data?.role) ||
    task.data?.assignee_id === user?.id;

  /** Persist task edits and let the backend own completed_at changes. */
  async function onSubmit(values: TaskFormValues) {
    try {
      const payload = taskPayload(values, true);
      await updateTask.mutateAsync(
        canManageAllTasks(organization.data?.role)
          ? payload
          : { ...payload, assignee_id: undefined },
      );
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  if (task.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading task.
      </p>
    );
  }

  if (task.isError) {
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={task.error} />
        <BackToProjectTasks projectId={undefined} />
        <h1 className="text-2xl font-semibold">Task not available</h1>
        <ErrorNotice error={task.error} />
      </section>
    );
  }

  if (!task.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  return (
    <section className="space-y-6">
      <BackToProjectTasks projectId={task.data.project_id} />
      <div className="rounded-md border border-line bg-white p-6 shadow-panel">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="break-words text-2xl font-semibold">
              {task.data.title}
            </h1>
            <p className="mt-2 text-muted">
              {project.data?.name ?? "Project task"}
            </p>
          </div>
          {task.data.completed_at ? (
            <span className="inline-flex items-center gap-2 rounded-md bg-green-50 px-2 py-1 text-xs font-semibold text-brand">
              <CheckCircle2 aria-hidden="true" className="h-4 w-4" />
              Completed
            </span>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-md border border-line bg-white p-5">
          <h2 className="font-semibold">Task details</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-muted">Description</dt>
              <dd className="break-words font-medium">
                {task.data.description || "No description"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Status</dt>
              <dd className="font-medium">{optionLabel(task.data.status)}</dd>
            </div>
            <div>
              <dt className="text-muted">Priority</dt>
              <dd className="font-medium">{optionLabel(task.data.priority)}</dd>
            </div>
            <div>
              <dt className="text-muted">Assignee</dt>
              <dd className="font-medium">
                {assigneeLabel(task.data.assignee_id, members.data?.items)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Due date</dt>
              <dd className="font-medium">{formatDate(task.data.due_date)}</dd>
            </div>
            <div>
              <dt className="text-muted">Completed</dt>
              <dd className="font-medium">
                {formatDateTime(task.data.completed_at)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Type</dt>
              <dd className="font-medium">
                {optionLabel(task.data.task_type)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Effort</dt>
              <dd className="font-medium">
                Estimated {task.data.estimated_hours ?? "0"}h / actual{" "}
                {task.data.actual_hours ?? "0"}h
              </dd>
            </div>
            <div>
              <dt className="text-muted">External reference</dt>
              <dd className="break-words font-medium">
                {task.data.external_reference || "Not set"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Blocked reason</dt>
              <dd className="break-words font-medium">
                {task.data.blocked_reason || "Not blocked"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Watchers</dt>
              <dd className="break-words font-medium">
                {task.data.watcher_ids
                  .map((watcherId) =>
                    assigneeLabel(watcherId, members.data?.items),
                  )
                  .join(", ") || "None"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Labels</dt>
              <dd className="mt-1 font-medium">
                <TaskLabelChips labels={task.data.labels} />
              </dd>
            </div>
            <div>
              <dt className="text-muted">Created</dt>
              <dd className="font-medium">
                {formatDateTime(task.data.created_at)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Updated</dt>
              <dd className="font-medium">
                {formatDateTime(task.data.updated_at)}
              </dd>
            </div>
          </dl>
        </article>

        <article className="rounded-md border border-line bg-white p-5">
          <h2 className="font-semibold">Update task</h2>
          {canEdit ? (
            <>
              <TaskForm
                form={form}
                submitLabel="Save task"
                isPending={updateTask.isPending}
                actorRole={organization.data?.role}
                userId={user?.id}
                members={canUseMemberList ? members.data?.items : undefined}
                includeStatus
                onSubmit={onSubmit}
              />
              {updateTask.isSuccess ? (
                <p
                  role="status"
                  className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-brand"
                >
                  Task updated.
                </p>
              ) : null}
              {updateTask.isError ? (
                <div className="mt-4">
                  <ErrorNotice error={updateTask.error} />
                </div>
              ) : null}
              <TaskLabelAssignmentPanel
                activeLabels={labels.data?.items.filter(
                  (label) => label.archived_at === null,
                )}
                assignedLabels={task.data.labels}
                isPending={
                  applyTaskLabel.isPending || removeTaskLabel.isPending
                }
                onApply={(labelId) => applyTaskLabel.mutateAsync(labelId)}
                onRemove={(labelId) => removeTaskLabel.mutateAsync(labelId)}
                error={applyTaskLabel.error ?? removeTaskLabel.error}
              />
            </>
          ) : (
            <p className="mt-4 text-sm text-muted">
              This task is read-only for your current role.
            </p>
          )}
        </article>
      </div>
    </section>
  );
}

/** Render active label assignment controls for editable task detail. */
function TaskLabelAssignmentPanel({
  activeLabels,
  assignedLabels,
  isPending,
  onApply,
  onRemove,
  error,
}: {
  activeLabels: TaskLabel[] | undefined;
  assignedLabels: TaskLabel[];
  isPending: boolean;
  onApply: (labelId: string) => Promise<unknown>;
  onRemove: (labelId: string) => Promise<unknown>;
  error: unknown;
}) {
  const assignedIds = new Set(assignedLabels.map((label) => label.id));
  return (
    <div className="mt-5 border-t border-line pt-4">
      <h3 className="flex items-center gap-2 text-sm font-semibold">
        <Tag aria-hidden="true" className="h-4 w-4" />
        Labels
      </h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {activeLabels?.length === 0 ? (
          <p className="text-sm text-muted">No active labels available.</p>
        ) : null}
        {activeLabels?.map((label) => {
          const isAssigned = assignedIds.has(label.id);
          return (
            <button
              key={label.id}
              type="button"
              disabled={isPending}
              className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-70 ${
                isAssigned
                  ? "border-brand bg-green-50 text-brand"
                  : "border-line hover:bg-surface"
              }`}
              onClick={() =>
                void (isAssigned ? onRemove(label.id) : onApply(label.id))
              }
            >
              <span
                aria-hidden="true"
                className="h-3 w-3 rounded-sm"
                style={{ backgroundColor: label.color }}
              />
              {label.name}
            </button>
          );
        })}
      </div>
      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}
    </div>
  );
}

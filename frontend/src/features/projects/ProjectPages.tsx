// Route pages for project list, creation, detail, and settings.

import { zodResolver } from "@hookform/resolvers/zod";
import {
  Archive,
  ArrowLeft,
  ClipboardList,
  FolderKanban,
  Save,
  Tag,
  UserPlus,
  UsersRound,
} from "lucide-react";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { UseFormRegisterReturn, useForm } from "react-hook-form";
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
import { useOrganization } from "../organizations/api";
import { useOrganizationMembers } from "../organizations/api";
import {
  OrganizationMembership,
  OrganizationRole,
  PaginatedResponse,
  PaginationParams,
} from "../organizations/types";
import {
  useCreateProject,
  useCreateProjectInvitation,
  useOrganizationProjects,
  useProject,
  useProjectMembers,
  useRemoveProjectMember,
  useUpdateProject,
} from "./api";
import {
  Project,
  ProjectMembership,
  ProjectStatus,
  ProjectVisibility,
} from "./types";
import {
  useCreateProjectLabel,
  useProjectLabels,
  useUpdateProjectLabel,
} from "../tasks/api";
import { TaskLabel } from "../tasks/types";

const projectStatuses = [
  "planned",
  "active",
  "on_hold",
  "completed",
  "cancelled",
] as const satisfies readonly ProjectStatus[];

const projectVisibilities = [
  "organization",
  "project_members",
] as const satisfies readonly ProjectVisibility[];
const labelHexColorPattern = /^#[0-9A-F]{6}$/i;

const projectSchema = z.object({
  name: z.string().trim().min(1, "Project name is required.").max(160),
  description: z.string().trim().optional(),
  status: z.enum(projectStatuses),
  start_date: z.string().trim().optional(),
  end_date: z.string().trim().optional(),
  budget_amount: z.string().trim().optional(),
  budget_currency: z.string().trim().max(3).optional(),
  visibility: z.enum(projectVisibilities),
  project_owner_id: z.string().trim().optional(),
});

type ProjectFormValues = z.infer<typeof projectSchema>;
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

/** Read items from paginated API data while tolerating older list mocks in tests. */
function paginatedItems<TItem>(
  data: PaginatedResponse<TItem> | TItem[] | undefined,
) {
  if (!data) {
    return [];
  }
  return Array.isArray(data) ? data : (data.items ?? []);
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

/** Identify auth-loss responses from project and task API calls. */
function isAuthLoss(error: unknown) {
  return error instanceof ApiError && error.status === 401;
}

/** Clear cached session state and send the user back to login. */
function useFeatureAuthLoss() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  /** Keep 401 handling consistent across SPEC-106 queries and mutations. */
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

/** Redirect to login whenever a SPEC-106 query reports auth loss. */
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

/** Return true when the actor can manage project settings. */
function canManageProjects(role: OrganizationRole | undefined) {
  return role === "owner" || role === "admin";
}

/** Build the payload accepted by create and update project endpoints. */
function projectPayload(values: ProjectFormValues) {
  const description = values.description?.trim();
  const budgetAmount = values.budget_amount?.trim();
  const budgetCurrency = values.budget_currency?.trim();
  const projectOwnerId = values.project_owner_id?.trim();
  return {
    name: values.name.trim(),
    description: description ? description : null,
    status: values.status,
    start_date: values.start_date ? values.start_date : null,
    end_date: values.end_date ? values.end_date : null,
    budget_amount: budgetAmount ? budgetAmount : null,
    budget_currency: budgetCurrency ? budgetCurrency.toUpperCase() : null,
    visibility: values.visibility,
    project_owner_id: projectOwnerId ? projectOwnerId : null,
  };
}

/** Link back to one organization's projects with consistent styling. */
function BackToOrganizationProjects({
  organizationId,
}: {
  organizationId: string | undefined;
}) {
  return (
    <Link
      to={
        organizationId
          ? `/app/organizations/${organizationId}/projects`
          : "/app/organizations"
      }
      className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
    >
      <ArrowLeft aria-hidden="true" className="h-4 w-4" />
      Projects
    </Link>
  );
}

/** Render a compact archived/active state badge. */
function ProjectStateBadge({ project }: { project: Project }) {
  return (
    <span
      className={`inline-flex rounded-md px-2 py-1 text-xs font-semibold ${
        project.is_archived ? "bg-red-50 text-accent" : "bg-green-50 text-brand"
      }`}
    >
      {project.is_archived ? "Archived" : "Active"}
    </span>
  );
}

/** Show an organization's project list and role-aware create action. */
export function ProjectListPage() {
  const { organizationId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const pagination = paginationFromSearch(searchParams);
  const organization = useOrganization(organizationId);
  const projects = useOrganizationProjects(organizationId, pagination);

  /** Persist project pagination in the route query string. */
  function setPagination(nextPagination: PaginationParams) {
    const next = new URLSearchParams(searchParams);
    next.set("limit", String(nextPagination.limit));
    next.set("offset", String(nextPagination.offset));
    setSearchParams(next);
  }

  if (organization.isLoading || projects.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading projects.
      </p>
    );
  }

  if (organization.isError || projects.isError) {
    const error = organization.error ?? projects.error;
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={error} />
        <BackToOrganizationProjects organizationId={organizationId} />
        <h1 className="text-2xl font-semibold">Projects not available</h1>
        <ErrorNotice error={error} />
      </section>
    );
  }

  if (!organization.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  const items = projects.data?.items ?? [];
  const canCreate = canManageProjects(organization.data.role);

  return (
    <section className="space-y-6">
      <Link
        to={`/app/organizations/${organization.data.id}`}
        className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        {organization.data.name}
      </Link>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Projects</h1>
          <p className="mt-2 text-muted">
            Operational work streams for {organization.data.name}.
          </p>
        </div>
        {canCreate ? (
          <Link
            to={`/app/organizations/${organization.data.id}/projects/new`}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
          >
            <FolderKanban aria-hidden="true" className="h-4 w-4" />
            New project
          </Link>
        ) : null}
      </div>

      {items.length === 0 ? (
        <div className="rounded-md border border-line bg-white p-6 shadow-panel">
          <h2 className="text-lg font-semibold">No projects yet</h2>
          <p className="mt-2 max-w-xl text-sm text-muted">
            {canCreate
              ? "Create the first project for this workspace."
              : "Projects will appear here when an owner or admin creates them."}
          </p>
          {canCreate ? (
            <Link
              to={`/app/organizations/${organization.data.id}/projects/new`}
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
            >
              <FolderKanban aria-hidden="true" className="h-4 w-4" />
              New project
            </Link>
          ) : null}
        </div>
      ) : (
        <>
          <div className="grid gap-4 md:grid-cols-2">
            {items.map((project) => (
              <Link
                key={project.id}
                to={`/app/projects/${project.id}`}
                className="rounded-md border border-line bg-white p-5 shadow-panel hover:border-brand"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h2 className="break-words text-lg font-semibold">
                      {project.name}
                    </h2>
                    <p className="mt-2 line-clamp-2 text-sm text-muted">
                      {project.description || "No description"}
                    </p>
                  </div>
                  <ProjectStateBadge project={project} />
                </div>
                <p className="mt-4 text-xs text-muted">
                  Updated {formatDateTime(project.updated_at)}
                </p>
              </Link>
            ))}
          </div>
          {projects.data ? (
            <PaginationControls
              page={projects.data}
              onPageChange={setPagination}
            />
          ) : null}
        </>
      )}
    </section>
  );
}

/** Render project creation form and navigate to the created project. */
export function ProjectNewPage() {
  const { organizationId } = useParams();
  const navigate = useNavigate();
  const handleAuthLoss = useFeatureAuthLoss();
  const organization = useOrganization(organizationId);
  const members = useOrganizationMembers(
    organizationId,
    canManageProjects(organization.data?.role),
  );
  const createProject = useCreateProject(organizationId ?? "");
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: projectFormDefaults(),
  });

  /** Persist a new project through the backend create endpoint. */
  async function onSubmit(values: ProjectFormValues) {
    try {
      const project = await createProject.mutateAsync(projectPayload(values));
      navigate(`/app/projects/${project.id}`);
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  if (organization.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading organization.
      </p>
    );
  }

  if (organization.isError) {
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={organization.error} />
        <BackToOrganizationProjects organizationId={organizationId} />
        <ErrorNotice error={organization.error} />
      </section>
    );
  }

  if (!organization.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  if (!canManageProjects(organization.data.role)) {
    return (
      <section className="space-y-4">
        <BackToOrganizationProjects organizationId={organization.data.id} />
        <h1 className="text-2xl font-semibold">New project</h1>
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          Only organization owners and admins can create projects.
        </p>
      </section>
    );
  }

  return (
    <section className="max-w-2xl space-y-6">
      <BackToOrganizationProjects organizationId={organization.data.id} />
      <div className="rounded-md border border-line bg-white p-6 shadow-panel">
        <h1 className="text-2xl font-semibold">New project</h1>
        <ProjectForm
          form={form}
          submitLabel="Create project"
          isPending={createProject.isPending}
          members={members.data?.items}
          onSubmit={onSubmit}
        />
        {createProject.isError ? (
          <div className="mt-4">
            <ErrorNotice error={createProject.error} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

/** Shared project form fields for create and settings screens. */
function ProjectForm({
  form,
  submitLabel,
  isPending,
  onSubmit,
  members,
}: {
  form: ReturnType<typeof useForm<ProjectFormValues>>;
  submitLabel: string;
  isPending: boolean;
  members: OrganizationMembership[] | undefined;
  onSubmit: (values: ProjectFormValues) => Promise<void>;
}) {
  return (
    <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="project_name" className="block text-sm font-medium">
          Name
        </label>
        <input
          id="project_name"
          type="text"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          {...form.register("name")}
        />
        {form.formState.errors.name ? (
          <p className="mt-1 text-sm text-accent">
            {form.formState.errors.name.message}
          </p>
        ) : null}
      </div>
      <div>
        <label
          htmlFor="project_description"
          className="block text-sm font-medium"
        >
          Description
        </label>
        <textarea
          id="project_description"
          className="mt-1 min-h-28 w-full rounded-md border border-line px-3 py-2"
          {...form.register("description")}
        />
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <ProjectSelect
          id="project_status"
          label="Status"
          registration={form.register("status")}
          options={projectStatuses}
        />
        <ProjectSelect
          id="project_visibility"
          label="Visibility"
          registration={form.register("visibility")}
          options={projectVisibilities}
        />
        <div>
          <label
            htmlFor="project_start_date"
            className="block text-sm font-medium"
          >
            Start date
          </label>
          <input
            id="project_start_date"
            type="date"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("start_date")}
          />
        </div>
        <div>
          <label
            htmlFor="project_end_date"
            className="block text-sm font-medium"
          >
            End date
          </label>
          <input
            id="project_end_date"
            type="date"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("end_date")}
          />
        </div>
        <div>
          <label
            htmlFor="project_budget_amount"
            className="block text-sm font-medium"
          >
            Budget amount
          </label>
          <input
            id="project_budget_amount"
            type="number"
            min="0"
            step="0.01"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("budget_amount")}
          />
        </div>
        <div>
          <label
            htmlFor="project_budget_currency"
            className="block text-sm font-medium"
          >
            Budget currency
          </label>
          <input
            id="project_budget_currency"
            type="text"
            className="mt-1 w-full rounded-md border border-line px-3 py-2 uppercase"
            {...form.register("budget_currency")}
          />
        </div>
        <div>
          <label htmlFor="project_owner" className="block text-sm font-medium">
            Project owner
          </label>
          <select
            id="project_owner"
            className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
            {...form.register("project_owner_id")}
          >
            <option value="">Unassigned</option>
            {members?.map((member) => (
              <option key={member.user_id} value={member.user_id}>
                {member.user.full_name} ({member.user.email})
              </option>
            ))}
          </select>
        </div>
      </div>
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

/** Default project metadata form values for create and settings screens. */
function projectFormDefaults(): ProjectFormValues {
  return {
    name: "",
    description: "",
    status: "active",
    start_date: "",
    end_date: "",
    budget_amount: "",
    budget_currency: "",
    visibility: "organization",
    project_owner_id: "",
  };
}

/** Render a project enum select with shared labels. */
function ProjectSelect({
  id,
  label,
  registration,
  options,
}: {
  id: string;
  label: string;
  registration: UseFormRegisterReturn;
  options: readonly string[];
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium">
        {label}
      </label>
      <select
        id={id}
        className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
        {...registration}
      >
        {options.map((option) => (
          <option key={option} value={option}>
            {optionLabel(option)}
          </option>
        ))}
      </select>
    </div>
  );
}

/** Render project detail and task list entry point. */
export function ProjectDetailPage() {
  const { projectId } = useParams();
  const project = useProject(projectId);
  const organization = useOrganization(project.data?.organization_id);

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
        <BackToOrganizationProjects organizationId={undefined} />
        <h1 className="text-2xl font-semibold">Project not available</h1>
        <ErrorNotice error={project.error} />
      </section>
    );
  }

  if (!project.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  const canManage = canManageProjects(organization.data?.role);

  return (
    <section className="space-y-6">
      <BackToOrganizationProjects
        organizationId={project.data.organization_id}
      />
      <ProjectHeader project={project.data} />
      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-md border border-line bg-white p-5">
          <h2 className="font-semibold">Project details</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-muted">Description</dt>
              <dd className="break-words font-medium">
                {project.data.description || "No description"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Status</dt>
              <dd className="font-medium">
                {optionLabel(project.data.status)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Visibility</dt>
              <dd className="font-medium">
                {optionLabel(project.data.visibility)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Dates</dt>
              <dd className="font-medium">
                {project.data.start_date || "Not set"} to{" "}
                {project.data.end_date || "Not set"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Budget</dt>
              <dd className="font-medium">
                {project.data.budget_amount && project.data.budget_currency
                  ? `${project.data.budget_amount} ${project.data.budget_currency}`
                  : "Not set"}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Created</dt>
              <dd className="font-medium">
                {formatDateTime(project.data.created_at)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Updated</dt>
              <dd className="font-medium">
                {formatDateTime(project.data.updated_at)}
              </dd>
            </div>
          </dl>
        </article>
        <article className="rounded-md border border-line bg-white p-5">
          <h2 className="font-semibold">Work</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              to={`/app/projects/${project.data.id}/tasks`}
              className="inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand/90"
            >
              <ClipboardList aria-hidden="true" className="h-4 w-4" />
              Open tasks
            </Link>
            {canManage ? (
              <Link
                to={`/app/projects/${project.data.id}/settings`}
                className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface"
              >
                <Archive aria-hidden="true" className="h-4 w-4" />
                Settings
              </Link>
            ) : null}
          </div>
        </article>
      </div>
      <ProjectMembersPanel
        projectId={project.data.id}
        organizationId={project.data.organization_id}
        canManage={canManage}
      />
      <ProjectLabelsPanel projectId={project.data.id} />
    </section>
  );
}

/** Render explicit project members and owner/admin invite controls. */
function ProjectMembersPanel({
  projectId,
  organizationId,
  canManage,
}: {
  projectId: string;
  organizationId: string;
  canManage: boolean;
}) {
  const projectMembers = useProjectMembers(projectId);
  const organizationMembers = useOrganizationMembers(organizationId, canManage);
  const invite = useCreateProjectInvitation(projectId);
  const removeProjectMember = useRemoveProjectMember(projectId);
  const [selectedUserId, setSelectedUserId] = useState("");
  const projectMemberItems = paginatedItems<ProjectMembership>(
    projectMembers.data,
  );
  const organizationMemberItems = paginatedItems<OrganizationMembership>(
    organizationMembers.data,
  );
  const projectMemberIds = new Set(
    projectMemberItems.map((member) => member.user_id),
  );
  const inviteOptions = organizationMemberItems.filter(
    (member) => !projectMemberIds.has(member.user_id),
  );

  /** Create a pending invitation for project access. */
  async function handleProjectInvite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedUserId) {
      return;
    }
    await invite.mutateAsync(selectedUserId);
    setSelectedUserId("");
  }

  return (
    <div className="rounded-md border border-line bg-white p-6 shadow-panel">
      <div className="flex items-center gap-2">
        <UsersRound aria-hidden="true" className="h-5 w-5 text-brand" />
        <h2 className="text-lg font-semibold">Project members</h2>
      </div>
      {projectMembers.isLoading ? (
        <p className="mt-4 text-sm text-muted">Loading project members.</p>
      ) : null}
      {projectMembers.isError ? (
        <div className="mt-4">
          <ErrorNotice error={projectMembers.error} />
        </div>
      ) : null}
      <div className="mt-4 grid gap-3">
        {projectMemberItems.map((member) => (
          <div
            key={member.id}
            className="flex flex-col gap-3 rounded-md bg-surface p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div>
              <p className="font-medium">{member.user.full_name}</p>
              <p className="text-sm text-muted">
                {member.user.email} · {optionLabel(member.role)}
              </p>
            </div>
            {canManage ? (
              <button
                type="button"
                disabled={removeProjectMember.isPending}
                className="inline-flex items-center justify-center rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
                onClick={() => removeProjectMember.mutate(member.user_id)}
              >
                Remove
              </button>
            ) : null}
          </div>
        ))}
      </div>
      {canManage ? (
        <form
          className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-end"
          onSubmit={handleProjectInvite}
        >
          <div className="min-w-0 flex-1">
            <label
              htmlFor="project_invite_user"
              className="block text-sm font-medium"
            >
              Add project member
            </label>
            <select
              id="project_invite_user"
              value={selectedUserId}
              onChange={(event) => setSelectedUserId(event.target.value)}
              className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
            >
              <option value="">Select organization member</option>
              {inviteOptions.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {member.user.full_name} ({member.user.email})
                </option>
              ))}
            </select>
          </div>
          <button
            type="submit"
            disabled={!selectedUserId || invite.isPending}
            className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            <UserPlus aria-hidden="true" className="h-4 w-4" />
            {invite.isPending ? "Inviting" : "Invite"}
          </button>
        </form>
      ) : null}
      {invite.isError ? (
        <div className="mt-4">
          <ErrorNotice error={invite.error} />
        </div>
      ) : null}
      {removeProjectMember.isError ? (
        <div className="mt-4">
          <ErrorNotice error={removeProjectMember.error} />
        </div>
      ) : null}
    </div>
  );
}

/** Show the project name and archive state. */
export function ProjectHeader({ project }: { project: Project }) {
  return (
    <div className="rounded-md border border-line bg-white p-6 shadow-panel">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="break-words text-2xl font-semibold">{project.name}</h1>
          <p className="mt-2 text-muted">Project workspace</p>
        </div>
        <ProjectStateBadge project={project} />
      </div>
    </div>
  );
}

/** Render owner/admin project settings and archive controls. */
export function ProjectSettingsPage() {
  const { projectId } = useParams();
  const handleAuthLoss = useFeatureAuthLoss();
  const project = useProject(projectId);
  const organization = useOrganization(project.data?.organization_id);
  const members = useOrganizationMembers(
    project.data?.organization_id,
    canManageProjects(organization.data?.role),
  );
  const updateProject = useUpdateProject(projectId ?? "");
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: projectFormDefaults(),
  });

  useEffect(() => {
    if (project.data) {
      form.reset({
        name: project.data.name,
        description: project.data.description ?? "",
        status: project.data.status,
        start_date: project.data.start_date ?? "",
        end_date: project.data.end_date ?? "",
        budget_amount: project.data.budget_amount ?? "",
        budget_currency: project.data.budget_currency ?? "",
        visibility: project.data.visibility,
        project_owner_id: project.data.project_owner_id ?? "",
      });
    }
  }, [form, project.data]);

  /** Persist owner/admin-editable project settings through the backend. */
  async function onSubmit(values: ProjectFormValues) {
    try {
      await updateProject.mutateAsync(projectPayload(values));
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  /** Toggle project archive state through the backend. */
  async function onArchiveToggle() {
    if (!project.data) {
      return;
    }
    try {
      await updateProject.mutateAsync({
        is_archived: !project.data.is_archived,
      });
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  if (project.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading settings.
      </p>
    );
  }

  if (project.isError) {
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={project.error} />
        <BackToOrganizationProjects organizationId={undefined} />
        <ErrorNotice error={project.error} />
      </section>
    );
  }

  if (!project.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  if (!canManageProjects(organization.data?.role)) {
    return (
      <section className="space-y-4">
        <BackToOrganizationProjects
          organizationId={project.data.organization_id}
        />
        <ProjectHeader project={project.data} />
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          Only organization owners and admins can change project settings.
        </p>
      </section>
    );
  }

  return (
    <section className="max-w-3xl space-y-6">
      <BackToOrganizationProjects
        organizationId={project.data.organization_id}
      />
      <ProjectHeader project={project.data} />
      <div className="rounded-md border border-line bg-white p-6 shadow-panel">
        <h2 className="text-lg font-semibold">Settings</h2>
        <ProjectForm
          form={form}
          submitLabel="Save project"
          isPending={updateProject.isPending}
          members={members.data?.items}
          onSubmit={onSubmit}
        />
        {updateProject.isSuccess ? (
          <p
            role="status"
            className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-brand"
          >
            Project updated.
          </p>
        ) : null}
      </div>
      <div className="rounded-md border border-line bg-white p-6">
        <h2 className="text-lg font-semibold">
          {project.data.is_archived ? "Unarchive project" : "Archive project"}
        </h2>
        <p className="mt-2 text-sm text-muted">
          Archived projects stay readable but reject new task creation.
        </p>
        <button
          type="button"
          disabled={updateProject.isPending}
          className="mt-4 inline-flex items-center gap-2 rounded-md border border-line px-4 py-2 font-semibold hover:bg-surface disabled:cursor-not-allowed disabled:opacity-70"
          onClick={onArchiveToggle}
        >
          <Archive aria-hidden="true" className="h-4 w-4" />
          {project.data.is_archived ? "Unarchive project" : "Archive project"}
        </button>
        {updateProject.isError ? (
          <div className="mt-4">
            <ErrorNotice error={updateProject.error} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

/** Render project label management controls for project team members. */
function ProjectLabelsPanel({ projectId }: { projectId: string }) {
  const labels = useProjectLabels(projectId, true);
  const createLabel = useCreateProjectLabel(projectId);
  const updateLabel = useUpdateProjectLabel(projectId);
  const [name, setName] = useState("");
  const [color, setColor] = useState("#2563EB");
  const [description, setDescription] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);
  const isValidColor = labelHexColorPattern.test(color);

  /** Persist a new label through the project labels API. */
  async function onCreateLabel(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!isValidColor) {
      setValidationError("Label color must use #RRGGBB.");
      return;
    }
    setValidationError(null);
    await createLabel.mutateAsync({
      name: name.trim(),
      color: color.toUpperCase(),
      description: description.trim() ? description.trim() : null,
    });
    setName("");
    setColor("#2563EB");
    setDescription("");
  }

  /** Toggle the archived state for one project label. */
  async function onToggleArchive(label: TaskLabel) {
    await updateLabel.mutateAsync({
      labelId: label.id,
      payload: { is_archived: label.archived_at === null },
    });
  }

  return (
    <div className="rounded-md border border-line bg-white p-6 shadow-panel">
      <h2 className="text-lg font-semibold">Labels</h2>
      <form
        className="mt-4 grid gap-3 sm:grid-cols-[1fr_8rem] lg:grid-cols-[1fr_8rem_1fr_auto]"
        onSubmit={onCreateLabel}
      >
        <div>
          <label htmlFor="label_name" className="block text-sm font-medium">
            Label name
          </label>
          <input
            id="label_name"
            type="text"
            maxLength={60}
            value={name}
            onChange={(event) => setName(event.target.value)}
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="label_color" className="block text-sm font-medium">
            Label color
          </label>
          <div className="mt-1 flex items-center gap-2">
            <span
              aria-hidden="true"
              className="h-8 w-8 rounded-md border border-line"
              style={{ backgroundColor: isValidColor ? color : "white" }}
            />
            <input
              id="label_color"
              type="text"
              maxLength={7}
              value={color}
              onChange={(event) => setColor(event.target.value.toUpperCase())}
              className="w-full rounded-md border border-line px-3 py-2 font-mono text-sm uppercase"
            />
          </div>
          {validationError ? (
            <p className="mt-1 text-sm text-accent">{validationError}</p>
          ) : null}
        </div>
        <div>
          <label
            htmlFor="label_description"
            className="block text-sm font-medium"
          >
            Label description
          </label>
          <input
            id="label_description"
            type="text"
            maxLength={500}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
          />
        </div>
        <button
          type="submit"
          disabled={createLabel.isPending || !name.trim()}
          className="self-end inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <Tag aria-hidden="true" className="h-4 w-4" />
          Add
        </button>
      </form>
      {createLabel.isError ? (
        <div className="mt-4">
          <ErrorNotice error={createLabel.error} />
        </div>
      ) : null}
      <div className="mt-5 space-y-2">
        {labels.isLoading ? (
          <p className="text-sm text-muted">Loading labels.</p>
        ) : null}
        {labels.data?.items.length === 0 ? (
          <p className="text-sm text-muted">No labels yet.</p>
        ) : null}
        {labels.data?.items.map((label) => (
          <div
            key={label.id}
            className="flex flex-col gap-3 rounded-md border border-line bg-surface p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className={label.archived_at ? "opacity-60" : undefined}>
              <span className="inline-flex items-center gap-2 rounded-md bg-white px-2 py-1 text-sm font-semibold">
                <span
                  aria-hidden="true"
                  className="h-3 w-3 rounded-sm"
                  style={{ backgroundColor: label.color }}
                />
                {label.name}
              </span>
              {label.description ? (
                <p className="mt-2 text-sm text-muted">{label.description}</p>
              ) : null}
            </div>
            <button
              type="button"
              disabled={updateLabel.isPending}
              className="inline-flex items-center justify-center rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-white disabled:cursor-not-allowed disabled:opacity-70"
              onClick={() => void onToggleArchive(label)}
            >
              {label.archived_at ? "Restore" : "Archive"}
            </button>
          </div>
        ))}
      </div>
      {updateLabel.isError ? (
        <div className="mt-4">
          <ErrorNotice error={updateLabel.error} />
        </div>
      ) : null}
    </div>
  );
}

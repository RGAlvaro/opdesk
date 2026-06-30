// Route pages for project list, creation, detail, and settings.

import { zodResolver } from "@hookform/resolvers/zod";
import {
  Archive,
  ArrowLeft,
  ClipboardList,
  FolderKanban,
  Save,
} from "lucide-react";
import { useCallback, useEffect } from "react";
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
import { useOrganization } from "../organizations/api";
import {
  PaginatedResponse,
  PaginationParams,
  OrganizationRole,
} from "../organizations/types";
import {
  useCreateProject,
  useOrganizationProjects,
  useProject,
  useUpdateProject,
} from "./api";
import { Project } from "./types";

const projectSchema = z.object({
  name: z.string().trim().min(1, "Project name is required.").max(160),
  description: z.string().trim().optional(),
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

/** Return true when the actor can manage project settings. */
function canManageProjects(role: OrganizationRole | undefined) {
  return role === "owner" || role === "admin";
}

/** Build the payload accepted by create and update project endpoints. */
function projectPayload(values: ProjectFormValues) {
  const description = values.description?.trim();
  return {
    name: values.name.trim(),
    description: description ? description : null,
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
  const createProject = useCreateProject(organizationId ?? "");
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: { name: "", description: "" },
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
}: {
  form: ReturnType<typeof useForm<ProjectFormValues>>;
  submitLabel: string;
  isPending: boolean;
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
    </section>
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
  const updateProject = useUpdateProject(projectId ?? "");
  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: { name: "", description: "" },
  });

  useEffect(() => {
    if (project.data) {
      form.reset({
        name: project.data.name,
        description: project.data.description ?? "",
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

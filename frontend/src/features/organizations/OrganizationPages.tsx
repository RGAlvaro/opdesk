// Route pages for organization list, detail, settings, and member management.

import { zodResolver } from "@hookform/resolvers/zod";
import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  FolderKanban,
  Save,
  ShieldCheck,
  Trash2,
  UserCog,
  UsersRound,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { useQueryClient } from "@tanstack/react-query";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { z } from "zod";

import { ApiError, getErrorMessage } from "../../shared/api";
import { sessionQueryKey, useSession } from "../auth/session";
import {
  useCreateOrganization,
  useDeleteOrganization,
  useOrganization,
  useOrganizationMembers,
  useOrganizations,
  useRemoveMember,
  useTransferOwnership,
  useUpdateMemberRole,
  useUpdateOrganization,
} from "./api";
import {
  Organization,
  OrganizationMembership,
  OrganizationRole,
} from "./types";

const organizationSchema = z.object({
  name: z.string().trim().min(1, "Organization name is required.").max(120),
  slug: z.string().trim().max(120).optional(),
});

const settingsSchema = organizationSchema.extend({
  confirm_delete: z.string().trim().optional(),
});

type OrganizationFormValues = z.infer<typeof organizationSchema>;
type SettingsFormValues = z.infer<typeof settingsSchema>;

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

/** Identify auth-loss responses from organization API calls. */
function isAuthLoss(error: unknown) {
  return error instanceof ApiError && error.status === 401;
}

/** Clear cached session state and send the user back to login. */
function useOrganizationAuthLoss() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  /** Keep organization 401 handling consistent across queries and mutations. */
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

/** Redirect to login whenever an organization query reports auth loss. */
function AuthErrorRedirect({ error }: { error: unknown }) {
  const handleAuthLoss = useOrganizationAuthLoss();

  useEffect(() => {
    void handleAuthLoss(error);
  }, [error, handleAuthLoss]);

  if (isAuthLoss(error)) {
    return null;
  }
  return null;
}

/** Convert backend role values into stable display labels. */
function roleLabel(role: OrganizationRole) {
  const labels: Record<OrganizationRole, string> = {
    owner: "Owner",
    admin: "Admin",
    member: "Member",
  };
  return labels[role];
}

/** Format backend timestamps without taking ownership of business meaning. */
function formatDateTime(value: string | undefined) {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

/** Build the payload accepted by create and update organization endpoints. */
function organizationPayload(values: OrganizationFormValues) {
  const slug = values.slug?.trim();
  return {
    name: values.name.trim(),
    ...(slug ? { slug } : {}),
  };
}

/** Render a small status pill for owner/admin/member roles. */
function RoleBadge({ role }: { role: OrganizationRole }) {
  return (
    <span className="inline-flex rounded-md bg-surface px-2 py-1 text-xs font-semibold text-brand">
      {roleLabel(role)}
    </span>
  );
}

/** Link back to the organization list with consistent styling. */
function BackToOrganizations() {
  return (
    <Link
      to="/app/organizations"
      className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
    >
      <ArrowLeft aria-hidden="true" className="h-4 w-4" />
      Organizations
    </Link>
  );
}

/** Show the organization list, empty state, and create entry point. */
export function OrganizationListPage() {
  const organizations = useOrganizations();

  if (organizations.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading organizations.
      </p>
    );
  }

  if (organizations.isError) {
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={organizations.error} />
        <h1 className="text-2xl font-semibold">Organizations</h1>
        <ErrorNotice error={organizations.error} />
      </section>
    );
  }

  const items = organizations.data?.items ?? [];

  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Organizations</h1>
          <p className="mt-2 text-muted">
            Workspaces where your team manages operational work.
          </p>
        </div>
        <Link
          to="/app/organizations/new"
          className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
        >
          <Building2 aria-hidden="true" className="h-4 w-4" />
          New organization
        </Link>
      </div>

      {items.length === 0 ? (
        <div className="rounded-md border border-line bg-white p-6 shadow-panel">
          <h2 className="text-lg font-semibold">Create your first workspace</h2>
          <p className="mt-2 max-w-xl text-sm text-muted">
            Start with an organization so projects, members, and task work have
            a tenant boundary.
          </p>
          <Link
            to="/app/organizations/new"
            className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
          >
            <Building2 aria-hidden="true" className="h-4 w-4" />
            New organization
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {items.map((organization) => (
            <Link
              key={organization.id}
              to={`/app/organizations/${organization.id}`}
              className="rounded-md border border-line bg-white p-5 shadow-panel hover:border-brand"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{organization.name}</h2>
                  <p className="mt-1 text-sm text-muted">{organization.slug}</p>
                </div>
                <RoleBadge role={organization.role} />
              </div>
              <p className="mt-4 text-xs text-muted">
                Updated {formatDateTime(organization.updated_at)}
              </p>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

/** Render organization creation form and navigate to the created workspace. */
export function OrganizationNewPage() {
  const navigate = useNavigate();
  const handleAuthLoss = useOrganizationAuthLoss();
  const createOrganization = useCreateOrganization();
  const form = useForm<OrganizationFormValues>({
    resolver: zodResolver(organizationSchema),
    defaultValues: { name: "", slug: "" },
  });

  /** Persist a new organization through the backend create endpoint. */
  async function onSubmit(values: OrganizationFormValues) {
    try {
      const organization = await createOrganization.mutateAsync(
        organizationPayload(values),
      );
      navigate(`/app/organizations/${organization.id}`);
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  return (
    <section className="max-w-2xl space-y-6">
      <BackToOrganizations />
      <div className="rounded-md border border-line bg-white p-6 shadow-panel">
        <h1 className="text-2xl font-semibold">New organization</h1>
        <p className="mt-2 text-sm text-muted">
          Create a tenant workspace for your team.
        </p>
        <OrganizationForm
          form={form}
          submitLabel="Create organization"
          isPending={createOrganization.isPending}
          onSubmit={onSubmit}
        />
        {createOrganization.isError ? (
          <ErrorNotice error={createOrganization.error} />
        ) : null}
      </div>
    </section>
  );
}

/** Shared organization form fields for create and settings screens. */
function OrganizationForm({
  form,
  submitLabel,
  isPending,
  onSubmit,
}: {
  form: ReturnType<typeof useForm<OrganizationFormValues>>;
  submitLabel: string;
  isPending: boolean;
  onSubmit: (values: OrganizationFormValues) => Promise<void>;
}) {
  return (
    <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
      <div>
        <label
          htmlFor="organization_name"
          className="block text-sm font-medium"
        >
          Name
        </label>
        <input
          id="organization_name"
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
          htmlFor="organization_slug"
          className="block text-sm font-medium"
        >
          Slug
        </label>
        <input
          id="organization_slug"
          type="text"
          className="mt-1 w-full rounded-md border border-line px-3 py-2"
          {...form.register("slug")}
        />
        {form.formState.errors.slug ? (
          <p className="mt-1 text-sm text-accent">
            {form.formState.errors.slug.message}
          </p>
        ) : null}
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

/** Render organization detail and role-aware navigation to admin routes. */
export function OrganizationDetailPage() {
  const { organizationId } = useParams();
  const organization = useOrganization(organizationId);

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
        <BackToOrganizations />
        <h1 className="text-2xl font-semibold">Organization not available</h1>
        <ErrorNotice error={organization.error} />
      </section>
    );
  }

  if (!organization.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  const canManageSettings = organization.data.role === "owner";
  const canViewMembers =
    organization.data.role === "owner" || organization.data.role === "admin";

  return (
    <section className="space-y-6">
      <BackToOrganizations />
      <OrganizationHeader organization={organization.data} />
      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-md border border-line bg-white p-5">
          <h2 className="font-semibold">Workspace details</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="text-muted">Slug</dt>
              <dd className="font-medium">{organization.data.slug}</dd>
            </div>
            <div>
              <dt className="text-muted">Created</dt>
              <dd className="font-medium">
                {formatDateTime(organization.data.created_at)}
              </dd>
            </div>
            <div>
              <dt className="text-muted">Updated</dt>
              <dd className="font-medium">
                {formatDateTime(organization.data.updated_at)}
              </dd>
            </div>
          </dl>
        </article>

        <article className="rounded-md border border-line bg-white p-5">
          <h2 className="font-semibold">Workspace navigation</h2>
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              to={`/app/organizations/${organization.data.id}/projects`}
              className="inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand/90"
            >
              <FolderKanban aria-hidden="true" className="h-4 w-4" />
              Projects
            </Link>
            {canViewMembers ? (
              <Link
                to={`/app/organizations/${organization.data.id}/members`}
                className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface"
              >
                <UsersRound aria-hidden="true" className="h-4 w-4" />
                Members
              </Link>
            ) : null}
            {canManageSettings ? (
              <Link
                to={`/app/organizations/${organization.data.id}/settings`}
                className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface"
              >
                <UserCog aria-hidden="true" className="h-4 w-4" />
                Settings
              </Link>
            ) : null}
            {!canViewMembers && !canManageSettings ? (
              <p className="text-sm text-muted">
                Your role has read-only access to this workspace.
              </p>
            ) : null}
          </div>
        </article>
      </div>
    </section>
  );
}

/** Show the organization name, slug, and current user's role. */
function OrganizationHeader({ organization }: { organization: Organization }) {
  return (
    <div className="rounded-md border border-line bg-white p-6 shadow-panel">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{organization.name}</h1>
          <p className="mt-2 text-muted">Organization workspace</p>
        </div>
        <RoleBadge role={organization.role} />
      </div>
    </div>
  );
}

/** Render owner-only organization settings and permanent deletion controls. */
export function OrganizationSettingsPage() {
  const { organizationId } = useParams();
  const navigate = useNavigate();
  const handleAuthLoss = useOrganizationAuthLoss();
  const organization = useOrganization(organizationId);
  const updateOrganization = useUpdateOrganization(organizationId ?? "");
  const deleteOrganization = useDeleteOrganization(organizationId ?? "");
  const form = useForm<SettingsFormValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: { name: "", slug: "", confirm_delete: "" },
  });

  useEffect(() => {
    if (organization.data) {
      form.reset({
        name: organization.data.name,
        slug: organization.data.slug,
        confirm_delete: "",
      });
    }
  }, [form, organization.data]);

  const deleteConfirmation = form.watch("confirm_delete");
  const expectedConfirmation = organization.data?.slug ?? "";
  const canDelete = deleteConfirmation === expectedConfirmation;

  /** Persist owner-editable organization settings through the backend. */
  async function onSubmit(values: SettingsFormValues) {
    try {
      await updateOrganization.mutateAsync(organizationPayload(values));
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  /** Permanently delete the organization after explicit confirmation. */
  async function onDelete() {
    try {
      await deleteOrganization.mutateAsync();
      navigate("/app/organizations", { replace: true });
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  if (organization.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading settings.
      </p>
    );
  }

  if (organization.isError) {
    return (
      <section className="space-y-4">
        <AuthErrorRedirect error={organization.error} />
        <BackToOrganizations />
        <ErrorNotice error={organization.error} />
      </section>
    );
  }

  if (!organization.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  if (organization.data.role !== "owner") {
    return (
      <section className="space-y-4">
        <BackToOrganizations />
        <OrganizationHeader organization={organization.data} />
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          Only the organization owner can change settings.
        </p>
      </section>
    );
  }

  return (
    <section className="max-w-3xl space-y-6">
      <BackToOrganizations />
      <OrganizationHeader organization={organization.data} />
      <div className="rounded-md border border-line bg-white p-6 shadow-panel">
        <h2 className="text-lg font-semibold">Settings</h2>
        <OrganizationForm
          form={form}
          submitLabel="Save organization"
          isPending={updateOrganization.isPending}
          onSubmit={onSubmit}
        />
        {updateOrganization.isSuccess ? (
          <p
            role="status"
            className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-brand"
          >
            Organization updated.
          </p>
        ) : null}
        {updateOrganization.isError ? (
          <div className="mt-4">
            <ErrorNotice error={updateOrganization.error} />
          </div>
        ) : null}
      </div>

      <div className="rounded-md border border-red-200 bg-white p-6">
        <div className="flex items-start gap-3">
          <AlertTriangle
            aria-hidden="true"
            className="mt-1 h-5 w-5 text-accent"
          />
          <div>
            <h2 className="text-lg font-semibold">Delete organization</h2>
            <p className="mt-2 text-sm text-muted">
              Deleting the organization removes its workspace data and
              memberships. User accounts remain.
            </p>
          </div>
        </div>
        <div className="mt-4">
          <label htmlFor="confirm_delete" className="block text-sm font-medium">
            Type {expectedConfirmation} to confirm
          </label>
          <input
            id="confirm_delete"
            type="text"
            className="mt-1 w-full rounded-md border border-line px-3 py-2"
            {...form.register("confirm_delete")}
          />
        </div>
        <button
          type="button"
          disabled={!canDelete || deleteOrganization.isPending}
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 font-semibold text-white hover:bg-accent/90 disabled:cursor-not-allowed disabled:opacity-70"
          onClick={onDelete}
        >
          <Trash2 aria-hidden="true" className="h-4 w-4" />
          {deleteOrganization.isPending ? "Deleting" : "Delete organization"}
        </button>
        {deleteOrganization.isError ? (
          <div className="mt-4">
            <ErrorNotice error={deleteOrganization.error} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

/** Render organization members and owner-only membership actions. */
export function OrganizationMembersPage() {
  const { organizationId } = useParams();
  const organization = useOrganization(organizationId);
  const canViewMembers =
    organization.data?.role === "owner" || organization.data?.role === "admin";

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
        <BackToOrganizations />
        <ErrorNotice error={organization.error} />
      </section>
    );
  }

  if (!organization.data) {
    return <Navigate to="/app/organizations" replace />;
  }

  if (!canViewMembers) {
    return (
      <section className="space-y-4">
        <BackToOrganizations />
        <OrganizationHeader organization={organization.data} />
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          Only organization owners and admins can view members.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <BackToOrganizations />
      <OrganizationHeader organization={organization.data} />
      <OrganizationMembersPanel organization={organization.data} />
    </section>
  );
}

/** Fetch and render the member list after role access is known. */
function OrganizationMembersPanel({
  organization,
}: {
  organization: Organization;
}) {
  const members = useOrganizationMembers(organization.id, true);

  return (
    <div className="rounded-md border border-line bg-white p-6 shadow-panel">
      <h2 className="text-lg font-semibold">Members</h2>
      {members.isLoading ? (
        <p className="mt-4 text-sm text-muted">Loading members.</p>
      ) : null}
      {members.isError ? (
        <>
          <AuthErrorRedirect error={members.error} />
          <div className="mt-4">
            <ErrorNotice error={members.error} />
          </div>
        </>
      ) : null}
      {members.data ? (
        <MemberList
          organizationId={organization.id}
          actorRole={organization.role}
          members={members.data.items}
        />
      ) : null}
    </div>
  );
}

/** Render membership rows with owner-only role, removal, and transfer controls. */
function MemberList({
  organizationId,
  actorRole,
  members,
}: {
  organizationId: string;
  actorRole: OrganizationRole;
  members: OrganizationMembership[];
}) {
  const { data: user } = useSession();
  const [memberToRemove, setMemberToRemove] = useState("");
  const [transferTarget, setTransferTarget] = useState("");
  const updateRole = useUpdateMemberRole(organizationId);
  const removeMember = useRemoveMember(organizationId);
  const transferOwnership = useTransferOwnership(organizationId);
  const handleAuthLoss = useOrganizationAuthLoss();
  const isOwnerActor = actorRole === "owner";
  const nonOwnerMembers = useMemo(
    () => members.filter((member) => member.role !== "owner"),
    [members],
  );

  /** Persist a role change for a non-owner membership row. */
  async function handleRoleChange(
    member: OrganizationMembership,
    role: Exclude<OrganizationRole, "owner">,
  ) {
    try {
      await updateRole.mutateAsync({ userId: member.user_id, role });
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  /** Remove the currently confirmed member from the organization. */
  async function handleRemoveMember(member: OrganizationMembership) {
    try {
      await removeMember.mutateAsync(member.user_id);
      setMemberToRemove("");
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  /** Transfer organization ownership to the selected target member. */
  async function handleTransferOwnership() {
    try {
      await transferOwnership.mutateAsync(transferTarget);
      setTransferTarget("");
    } catch (error) {
      await handleAuthLoss(error);
    }
  }

  return (
    <div className="mt-4 space-y-6">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] border-separate border-spacing-y-2 text-left text-sm">
          <thead className="text-muted">
            <tr>
              <th className="px-3 py-2 font-medium">Member</th>
              <th className="px-3 py-2 font-medium">Role</th>
              <th className="px-3 py-2 font-medium">Status</th>
              <th className="px-3 py-2 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {members.map((member) => {
              const canManageMember = isOwnerActor && member.role !== "owner";
              const isCurrentUser = member.user_id === user?.id;
              return (
                <tr key={member.id} className="bg-surface">
                  <td className="rounded-l-md px-3 py-3">
                    <div className="font-medium">{member.user.full_name}</div>
                    <div className="text-muted">{member.user.email}</div>
                  </td>
                  <td className="px-3 py-3">
                    <RoleBadge role={member.role} />
                  </td>
                  <td className="px-3 py-3">
                    {member.user.is_active ? "Active" : "Inactive"}
                    {isCurrentUser ? (
                      <span className="ml-2 text-muted">You</span>
                    ) : null}
                  </td>
                  <td className="rounded-r-md px-3 py-3">
                    {canManageMember ? (
                      <div className="flex flex-wrap items-center gap-2">
                        <label
                          className="sr-only"
                          htmlFor={`role-${member.user_id}`}
                        >
                          Role for {member.user.email}
                        </label>
                        <select
                          id={`role-${member.user_id}`}
                          className="rounded-md border border-line bg-white px-2 py-1"
                          value={member.role}
                          disabled={updateRole.isPending}
                          onChange={(event) =>
                            handleRoleChange(
                              member,
                              event.target.value as Exclude<
                                OrganizationRole,
                                "owner"
                              >,
                            )
                          }
                        >
                          <option value="admin">Admin</option>
                          <option value="member">Member</option>
                        </select>
                        <button
                          type="button"
                          className="rounded-md border border-line px-2 py-1 font-medium hover:bg-white"
                          onClick={() => setMemberToRemove(member.user_id)}
                        >
                          Remove
                        </button>
                        {memberToRemove === member.user_id ? (
                          <button
                            type="button"
                            className="rounded-md bg-accent px-2 py-1 font-medium text-white disabled:opacity-70"
                            disabled={removeMember.isPending}
                            onClick={() => handleRemoveMember(member)}
                          >
                            Confirm remove
                          </button>
                        ) : null}
                      </div>
                    ) : (
                      <span className="text-muted">No actions</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {isOwnerActor ? (
        <div className="rounded-md border border-line p-4">
          <div className="flex items-start gap-3">
            <ShieldCheck
              aria-hidden="true"
              className="mt-1 h-5 w-5 text-brand"
            />
            <div>
              <h3 className="font-semibold">Transfer ownership</h3>
              <p className="mt-1 text-sm text-muted">
                Select an existing non-owner member to become the sole owner.
              </p>
            </div>
          </div>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <label className="sr-only" htmlFor="transfer_owner">
              New owner
            </label>
            <select
              id="transfer_owner"
              className="rounded-md border border-line bg-white px-3 py-2"
              value={transferTarget}
              onChange={(event) => setTransferTarget(event.target.value)}
            >
              <option value="">Select member</option>
              {nonOwnerMembers.map((member) => (
                <option key={member.user_id} value={member.user_id}>
                  {member.user.full_name} ({member.user.email})
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={!transferTarget || transferOwnership.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
              onClick={handleTransferOwnership}
            >
              <ShieldCheck aria-hidden="true" className="h-4 w-4" />
              {transferOwnership.isPending
                ? "Transferring"
                : "Transfer ownership"}
            </button>
          </div>
        </div>
      ) : null}

      {updateRole.isError ? <ErrorNotice error={updateRole.error} /> : null}
      {removeMember.isError ? <ErrorNotice error={removeMember.error} /> : null}
      {transferOwnership.isError ? (
        <ErrorNotice error={transferOwnership.error} />
      ) : null}
    </div>
  );
}

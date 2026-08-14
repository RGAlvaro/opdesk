// Minimal authenticated invitation inbox for SPEC-303 acceptance workflows.

import { Check, Mail, X } from "lucide-react";

import { getErrorMessage } from "../../shared/api";
import {
  useAcceptInvitation,
  useDeclineInvitation,
  useMyInvitations,
} from "./api";
import { Invitation } from "./types";

/** Render invitations addressed to the current user with accept/decline actions. */
export function MyInvitationsPage() {
  const invitations = useMyInvitations();
  const acceptInvitation = useAcceptInvitation();
  const declineInvitation = useDeclineInvitation();
  const pendingItems =
    invitations.data?.items.filter(
      (invitation) => invitation.status === "pending",
    ) ?? [];

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">My invitations</h1>
        <p className="mt-2 text-muted">Pending workspace and project access.</p>
      </div>
      {invitations.isLoading ? (
        <p className="rounded-md border border-line bg-white p-6">
          Loading invitations.
        </p>
      ) : null}
      {invitations.isError ? (
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          {getErrorMessage(invitations.error)}
        </p>
      ) : null}
      {pendingItems.length === 0 && invitations.isSuccess ? (
        <div className="rounded-md border border-line bg-white p-6 shadow-panel">
          <Mail aria-hidden="true" className="h-5 w-5 text-brand" />
          <h2 className="mt-3 text-lg font-semibold">No pending invitations</h2>
        </div>
      ) : null}
      <div className="grid gap-4">
        {pendingItems.map((invitation) => (
          <InvitationCard
            key={invitation.id}
            invitation={invitation}
            isAccepting={acceptInvitation.isPending}
            isDeclining={declineInvitation.isPending}
            onAccept={() => acceptInvitation.mutate(invitation.id)}
            onDecline={() => declineInvitation.mutate(invitation.id)}
          />
        ))}
      </div>
      {acceptInvitation.isError ? (
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          {getErrorMessage(acceptInvitation.error)}
        </p>
      ) : null}
      {declineInvitation.isError ? (
        <p
          role="alert"
          className="rounded-md bg-red-50 px-3 py-2 text-sm text-accent"
        >
          {getErrorMessage(declineInvitation.error)}
        </p>
      ) : null}
    </section>
  );
}

/** Render one pending invitation with safe organization/project names. */
function InvitationCard({
  invitation,
  isAccepting,
  isDeclining,
  onAccept,
  onDecline,
}: {
  invitation: Invitation;
  isAccepting: boolean;
  isDeclining: boolean;
  onAccept: () => void;
  onDecline: () => void;
}) {
  const title =
    invitation.scope_type === "organization"
      ? (invitation.organization_name ?? "Organization invitation")
      : (invitation.project_name ?? "Project invitation");
  const subtitle =
    invitation.scope_type === "organization"
      ? `Role: ${invitation.role ?? "member"}`
      : (invitation.organization_name ?? "Project access");

  return (
    <article className="rounded-md border border-line bg-white p-5 shadow-panel">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">
            {invitation.scope_type === "organization"
              ? "Organization"
              : "Project"}
          </p>
          <h2 className="mt-1 text-lg font-semibold">{title}</h2>
          <p className="mt-1 text-sm text-muted">{subtitle}</p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            disabled={isAccepting || isDeclining}
            className="inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
            onClick={onAccept}
          >
            <Check aria-hidden="true" className="h-4 w-4" />
            Accept
          </button>
          <button
            type="button"
            disabled={isAccepting || isDeclining}
            className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface disabled:cursor-not-allowed disabled:opacity-70"
            onClick={onDecline}
          >
            <X aria-hidden="true" className="h-4 w-4" />
            Decline
          </button>
        </div>
      </div>
    </article>
  );
}

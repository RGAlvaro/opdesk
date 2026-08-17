// Route pages for client ticket tracking and internal ticket handling.

import { FormEvent, useEffect, useState } from "react";
import { ArrowLeft, Check, MessageSquare, Plus, Save, X } from "lucide-react";
import { Link, Navigate, useNavigate, useParams } from "react-router-dom";

import { getErrorMessage } from "../../shared/api";
import { useProjectMembers } from "../projects/api";
import {
  useClientProjects,
  useClientTicket,
  useClientTickets,
  useCreateClientTicket,
  useCreateTicketAssignmentRequest,
  useCreateTicketComment,
  useProjectTickets,
  useResolveTicketAssignmentRequest,
  useTicket,
  useTicketAssignmentRequests,
  useTicketComments,
  useUpdateTicket,
} from "./api";
import { Ticket } from "./types";
import { TaskPriority, TaskStatus } from "../tasks/types";

const defaultPagination = { limit: 20, offset: 0 };
const priorities = [
  "low",
  "medium",
  "high",
  "urgent",
] as const satisfies readonly TaskPriority[];
const statuses = [
  "todo",
  "in_progress",
  "blocked",
  "done",
  "cancelled",
] as const satisfies readonly TaskStatus[];

/** Render backend errors with the shared safe message. */
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

/** Convert enum strings into readable labels. */
function optionLabel(value: string | null | undefined) {
  if (!value) {
    return "Not set";
  }
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/** Format backend timestamps for compact ticket surfaces. */
function formatDateTime(value: string | undefined | null) {
  if (!value) {
    return "Not available";
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

/** Show a stable visual marker for tickets. */
function TicketBadge() {
  return (
    <span className="inline-flex rounded-md bg-amber-100 px-2 py-1 text-xs font-semibold text-amber-800">
      Ticket
    </span>
  );
}

/** Render a ticket list item for client and internal users. */
function TicketListItem({ ticket, to }: { ticket: Ticket; to: string }) {
  return (
    <Link
      to={to}
      className="block rounded-md border border-line bg-white p-4 shadow-panel hover:border-brand"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <TicketBadge />
            <h2 className="font-semibold">{ticket.title}</h2>
          </div>
          <p className="mt-2 line-clamp-2 text-sm text-muted">
            {ticket.description || "No description"}
          </p>
        </div>
        <span className="rounded-md bg-surface px-2 py-1 text-xs font-semibold">
          {optionLabel(ticket.status)}
        </span>
      </div>
      <p className="mt-3 text-xs text-muted">
        Updated {formatDateTime(ticket.updated_at)}
      </p>
    </Link>
  );
}

/** Client-facing ticket list and creation form. */
export function ClientTicketListPage() {
  const projects = useClientProjects();
  const tickets = useClientTickets(defaultPagination);
  const navigate = useNavigate();
  const [projectId, setProjectId] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const createTicket = useCreateClientTicket(projectId);

  /** Create a client ticket and navigate to its detail page. */
  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const ticket = await createTicket.mutateAsync({
      subject,
      description,
      priority,
    });
    navigate(`/app/client/tickets/${ticket.id}`);
  }

  if (projects.isLoading || tickets.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading tickets.
      </p>
    );
  }

  if (projects.isError || tickets.isError) {
    return <ErrorNotice error={projects.error ?? tickets.error} />;
  }

  const projectItems = projects.data?.items ?? [];
  const ticketItems = tickets.data?.items ?? [];

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">My tickets</h1>
        <p className="mt-2 text-muted">
          Track requests and feedback for your projects.
        </p>
      </div>
      <form
        className="rounded-md border border-line bg-white p-5 shadow-panel"
        onSubmit={handleSubmit}
      >
        <div className="flex items-center gap-2">
          <Plus aria-hidden="true" className="h-5 w-5 text-brand" />
          <h2 className="font-semibold">New ticket</h2>
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="block text-sm font-medium">
            Project
            <select
              className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
              value={projectId}
              onChange={(event) => setProjectId(event.target.value)}
              required
            >
              <option value="">Select project</option>
              {projectItems.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium">
            Priority
            <select
              className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
              value={priority}
              onChange={(event) =>
                setPriority(event.target.value as TaskPriority)
              }
            >
              {priorities.map((item) => (
                <option key={item} value={item}>
                  {optionLabel(item)}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-medium sm:col-span-2">
            Subject
            <input
              className="mt-1 w-full rounded-md border border-line px-3 py-2"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              required
            />
          </label>
          <label className="block text-sm font-medium sm:col-span-2">
            Description
            <textarea
              className="mt-1 min-h-28 w-full rounded-md border border-line px-3 py-2"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              required
            />
          </label>
        </div>
        {createTicket.isError ? (
          <div className="mt-4">
            <ErrorNotice error={createTicket.error} />
          </div>
        ) : null}
        <button
          type="submit"
          disabled={createTicket.isPending || projectItems.length === 0}
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          <Save aria-hidden="true" className="h-4 w-4" />
          {createTicket.isPending ? "Creating" : "Create ticket"}
        </button>
      </form>
      <div className="grid gap-4">
        {ticketItems.map((ticket) => (
          <TicketListItem
            key={ticket.id}
            ticket={ticket}
            to={`/app/client/tickets/${ticket.id}`}
          />
        ))}
        {ticketItems.length === 0 ? (
          <p className="rounded-md border border-line bg-white p-6 text-muted">
            No tickets yet.
          </p>
        ) : null}
      </div>
    </section>
  );
}

/** Internal project ticket list. */
export function InternalTicketListPage() {
  const { projectId } = useParams();
  const tickets = useProjectTickets(projectId, defaultPagination);

  if (tickets.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading tickets.
      </p>
    );
  }

  if (tickets.isError) {
    return <ErrorNotice error={tickets.error} />;
  }

  return (
    <section className="space-y-6">
      <Link
        to={projectId ? `/app/projects/${projectId}` : "/app/organizations"}
        className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        Project
      </Link>
      <div>
        <h1 className="text-2xl font-semibold">Tickets</h1>
        <p className="mt-2 text-muted">
          Client-created requests for this project.
        </p>
      </div>
      <div className="grid gap-4">
        {(tickets.data?.items ?? []).map((ticket) => (
          <TicketListItem
            key={ticket.id}
            ticket={ticket}
            to={`/app/tickets/${ticket.id}`}
          />
        ))}
        {tickets.data?.items.length === 0 ? (
          <p className="rounded-md border border-line bg-white p-6 text-muted">
            No client tickets yet.
          </p>
        ) : null}
      </div>
    </section>
  );
}

/** Shared ticket detail and comment thread. */
function TicketDetail({ client }: { client: boolean }) {
  const { ticketId } = useParams();
  const clientTicket = useClientTicket(client ? ticketId : undefined);
  const internalTicket = useTicket(client ? undefined : ticketId);
  const ticket = client ? clientTicket : internalTicket;
  const comments = useTicketComments(ticketId, client);
  const createComment = useCreateTicketComment(ticketId ?? "", client);
  const updateTicket = useUpdateTicket(ticketId ?? "");
  const createAssignmentRequest = useCreateTicketAssignmentRequest(
    ticketId ?? "",
  );
  const members = useProjectMembers(ticket.data?.project_id);
  const [comment, setComment] = useState("");
  const [status, setStatus] = useState<TaskStatus>("todo");
  const [assigneeId, setAssigneeId] = useState("");
  const [handoffTargetId, setHandoffTargetId] = useState("");

  useEffect(() => {
    if (!ticket.data) {
      return;
    }
    setStatus(ticket.data.status);
    setAssigneeId(ticket.data.assignee_id ?? "");
  }, [ticket.data]);

  /** Add one comment to the ticket thread. */
  async function handleComment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createComment.mutateAsync(comment);
    setComment("");
  }

  /** Persist owner/admin ticket status and assignment fields. */
  async function handleUpdate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await updateTicket.mutateAsync({
      status,
      assignee_id: assigneeId ? assigneeId : null,
    });
  }

  /** Request reassignment without changing the ticket until target acceptance. */
  async function handleHandoff(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createAssignmentRequest.mutateAsync({
      target_user_id: handoffTargetId,
    });
    setHandoffTargetId("");
  }

  if (ticket.isLoading || comments.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading ticket.
      </p>
    );
  }

  if (ticket.isError || comments.isError) {
    return <ErrorNotice error={ticket.error ?? comments.error} />;
  }

  if (!ticket.data) {
    return (
      <Navigate to={client ? "/app/client" : "/app/organizations"} replace />
    );
  }

  const memberItems = members.data?.items ?? [];
  const assignee = memberItems.find(
    (member) => member.user_id === ticket.data.assignee_id,
  );

  return (
    <section className="space-y-6">
      <Link
        to={
          client
            ? "/app/client"
            : `/app/projects/${ticket.data.project_id}/tickets`
        }
        className="inline-flex items-center gap-2 text-sm font-medium text-brand hover:underline"
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        Tickets
      </Link>
      <article className="rounded-md border border-line bg-white p-6 shadow-panel">
        <div className="flex flex-wrap items-center gap-2">
          <TicketBadge />
          <h1 className="text-2xl font-semibold">{ticket.data.title}</h1>
        </div>
        <p className="mt-3 whitespace-pre-wrap text-sm text-muted">
          {ticket.data.description}
        </p>
        <dl className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
          <div>
            <dt className="text-muted">Status</dt>
            <dd className="font-medium">{optionLabel(ticket.data.status)}</dd>
          </div>
          <div>
            <dt className="text-muted">Priority</dt>
            <dd className="font-medium">{optionLabel(ticket.data.priority)}</dd>
          </div>
          <div>
            <dt className="text-muted">Assignment</dt>
            <dd className="font-medium">
              {ticket.data.assignee_id
                ? (assignee?.user.full_name ?? "Assigned")
                : "Unassigned"}
            </dd>
          </div>
          <div>
            <dt className="text-muted">Updated</dt>
            <dd className="font-medium">
              {formatDateTime(ticket.data.updated_at)}
            </dd>
          </div>
        </dl>
      </article>
      {!client ? (
        <form
          className="rounded-md border border-line bg-white p-5 shadow-panel"
          onSubmit={handleUpdate}
        >
          <h2 className="font-semibold">Ticket handling</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-medium">
              Status
              <select
                className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
                value={status}
                onChange={(event) =>
                  setStatus(event.target.value as TaskStatus)
                }
              >
                {statuses.map((item) => (
                  <option key={item} value={item}>
                    {optionLabel(item)}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-medium">
              Assignee
              <select
                className="mt-1 w-full rounded-md border border-line bg-white px-3 py-2"
                value={assigneeId}
                onChange={(event) => setAssigneeId(event.target.value)}
              >
                <option value="">Unassigned</option>
                {memberItems.map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.user.full_name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          {updateTicket.isError ? (
            <div className="mt-4">
              <ErrorNotice error={updateTicket.error} />
            </div>
          ) : null}
          <button
            type="submit"
            className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
          >
            <Save aria-hidden="true" className="h-4 w-4" />
            Save ticket
          </button>
        </form>
      ) : null}
      {!client ? (
        <form
          className="rounded-md border border-line bg-white p-5 shadow-panel"
          onSubmit={handleHandoff}
        >
          <h2 className="font-semibold">Request reassignment</h2>
          <div className="mt-4 flex flex-col gap-3 sm:flex-row">
            <select
              aria-label="Target assignee"
              className="min-w-0 flex-1 rounded-md border border-line bg-white px-3 py-2"
              value={handoffTargetId}
              onChange={(event) => setHandoffTargetId(event.target.value)}
              required
            >
              <option value="">Select project member</option>
              {memberItems
                .filter((member) => member.user_id !== ticket.data.assignee_id)
                .map((member) => (
                  <option key={member.user_id} value={member.user_id}>
                    {member.user.full_name}
                  </option>
                ))}
            </select>
            <button
              type="submit"
              disabled={createAssignmentRequest.isPending}
              className="inline-flex items-center justify-center gap-2 rounded-md border border-line px-4 py-2 font-semibold hover:bg-surface disabled:cursor-not-allowed disabled:opacity-70"
            >
              <MessageSquare aria-hidden="true" className="h-4 w-4" />
              {createAssignmentRequest.isPending ? "Requesting" : "Request"}
            </button>
          </div>
          {createAssignmentRequest.isError ? (
            <div className="mt-4">
              <ErrorNotice error={createAssignmentRequest.error} />
            </div>
          ) : null}
          {createAssignmentRequest.isSuccess ? (
            <p
              role="status"
              className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-brand"
            >
              Assignment request sent.
            </p>
          ) : null}
        </form>
      ) : null}
      <section className="rounded-md border border-line bg-white p-5 shadow-panel">
        <div className="flex items-center gap-2">
          <MessageSquare aria-hidden="true" className="h-5 w-5 text-brand" />
          <h2 className="font-semibold">Feedback</h2>
        </div>
        <div className="mt-4 space-y-3">
          {(comments.data?.items ?? []).map((item) => (
            <article
              key={item.id}
              className="rounded-md border border-line p-3"
            >
              <p className="whitespace-pre-wrap text-sm">{item.body}</p>
              <p className="mt-2 text-xs text-muted">
                {formatDateTime(item.created_at)}
              </p>
            </article>
          ))}
        </div>
        <form className="mt-4 space-y-3" onSubmit={handleComment}>
          <textarea
            className="min-h-24 w-full rounded-md border border-line px-3 py-2"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            required
          />
          {createComment.isError ? (
            <ErrorNotice error={createComment.error} />
          ) : null}
          <button
            type="submit"
            className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90"
          >
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Add comment
          </button>
        </form>
      </section>
    </section>
  );
}

/** Client-owned ticket detail page. */
export function ClientTicketDetailPage() {
  return <TicketDetail client />;
}

/** Internal ticket detail page. */
export function InternalTicketDetailPage() {
  return <TicketDetail client={false} />;
}

/** Current worker queue for pending ticket handoff requests. */
export function TicketAssignmentRequestsPage() {
  const requests = useTicketAssignmentRequests();
  const accept = useResolveTicketAssignmentRequest("accept");
  const decline = useResolveTicketAssignmentRequest("decline");

  if (requests.isLoading) {
    return (
      <p className="rounded-md border border-line bg-white p-6">
        Loading assignment requests.
      </p>
    );
  }

  if (requests.isError) {
    return <ErrorNotice error={requests.error} />;
  }

  const items = requests.data?.items ?? [];

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Assignment requests</h1>
        <p className="mt-2 text-muted">
          Ticket handoffs waiting for your response.
        </p>
      </div>
      <div className="grid gap-4">
        {items.map((request) => (
          <article
            key={request.id}
            className="rounded-md border border-line bg-white p-5 shadow-panel"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <TicketBadge />
                <h2 className="mt-2 font-semibold">{request.ticket.title}</h2>
                <p className="mt-1 text-sm text-muted">
                  Requested {formatDateTime(request.created_at)}
                </p>
              </div>
              <Link
                to={`/app/tickets/${request.task_id}`}
                className="rounded-md border border-line px-3 py-2 text-sm font-medium hover:bg-surface"
              >
                Open ticket
              </Link>
            </div>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                disabled={accept.isPending || decline.isPending}
                className="inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 font-semibold text-white hover:bg-brand/90 disabled:cursor-not-allowed disabled:opacity-70"
                onClick={() => accept.mutate(request.id)}
              >
                <Check aria-hidden="true" className="h-4 w-4" />
                Accept
              </button>
              <button
                type="button"
                disabled={accept.isPending || decline.isPending}
                className="inline-flex items-center gap-2 rounded-md border border-line px-4 py-2 font-semibold hover:bg-surface disabled:cursor-not-allowed disabled:opacity-70"
                onClick={() => decline.mutate(request.id)}
              >
                <X aria-hidden="true" className="h-4 w-4" />
                Decline
              </button>
            </div>
          </article>
        ))}
        {items.length === 0 ? (
          <p className="rounded-md border border-line bg-white p-6 text-muted">
            No pending assignment requests.
          </p>
        ) : null}
      </div>
    </section>
  );
}

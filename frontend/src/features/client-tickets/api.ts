// React Query helpers for restricted client accounts, tickets, and comments.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import { PaginationParams } from "../organizations/types";
import {
  ClientProjectListResponse,
  ProjectClientAccess,
  ProjectClientListResponse,
  ProjectClientPayload,
  Ticket,
  TicketAssignmentRequest,
  TicketAssignmentRequestListResponse,
  TicketAssignmentRequestPayload,
  TicketComment,
  TicketCommentListResponse,
  TicketListResponse,
  TicketPayload,
  TicketUpdatePayload,
} from "./types";

const ticketStaleTimeMs = 30_000;

/** Build query parameters for paginated ticket endpoints. */
function paginationSearchParams(pagination: PaginationParams) {
  return new URLSearchParams({
    limit: String(pagination.limit),
    offset: String(pagination.offset),
  }).toString();
}

/** Build a stable key for one project's client list. */
export function projectClientsQueryKey(projectId: string) {
  return ["projects", projectId, "clients"] as const;
}

/** Build a stable key for one project's ticket list. */
export function projectTicketsQueryKey(projectId: string) {
  return ["projects", projectId, "tickets"] as const;
}

/** Build a stable key for one ticket. */
export function ticketQueryKey(ticketId: string) {
  return ["tickets", ticketId] as const;
}

/** Build a stable key for one ticket comment thread. */
export function ticketCommentsQueryKey(ticketId: string) {
  return ["tickets", ticketId, "comments"] as const;
}

/** Build a stable key for current-user ticket assignment requests. */
export function ticketAssignmentRequestsQueryKey() {
  return ["ticket-assignment-requests"] as const;
}

/** Keep project client access state in cache. */
export function useProjectClients(projectId: string | undefined) {
  return useQuery({
    queryKey: projectId
      ? projectClientsQueryKey(projectId)
      : ["projects", "missing", "clients"],
    queryFn: () =>
      apiRequest<ProjectClientListResponse>(
        `/api/v1/projects/${projectId}/clients?limit=100&offset=0`,
      ),
    enabled: Boolean(projectId),
    staleTime: ticketStaleTimeMs,
  });
}

/** Create or grant a restricted client account. */
export function useCreateProjectClient(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectClientPayload) =>
      apiRequest<ProjectClientAccess>(`/api/v1/projects/${projectId}/clients`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: projectClientsQueryKey(projectId),
      });
    },
  });
}

/** Revoke a project client access row. */
export function useRevokeProjectClient(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (clientAccessId: string) =>
      apiRequest<void>(
        `/api/v1/projects/${projectId}/clients/${clientAccessId}`,
        {
          method: "DELETE",
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: projectClientsQueryKey(projectId),
      });
    },
  });
}

/** Keep internal project ticket list in cache. */
export function useProjectTickets(
  projectId: string | undefined,
  pagination: PaginationParams,
) {
  return useQuery({
    queryKey: projectId
      ? [...projectTicketsQueryKey(projectId), pagination]
      : ["missing"],
    queryFn: () =>
      apiRequest<TicketListResponse>(
        `/api/v1/projects/${projectId}/tickets?${paginationSearchParams(pagination)}`,
      ),
    enabled: Boolean(projectId),
    staleTime: ticketStaleTimeMs,
  });
}

/** Keep one internal ticket detail in cache. */
export function useTicket(ticketId: string | undefined) {
  return useQuery({
    queryKey: ticketId ? ticketQueryKey(ticketId) : ["tickets", "missing"],
    queryFn: () => apiRequest<Ticket>(`/api/v1/tickets/${ticketId}`),
    enabled: Boolean(ticketId),
    staleTime: ticketStaleTimeMs,
  });
}

/** Update owner/admin-managed ticket fields. */
export function useUpdateTicket(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketUpdatePayload) =>
      apiRequest<Ticket>(`/api/v1/tickets/${ticketId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: (ticket) => {
      queryClient.setQueryData(ticketQueryKey(ticket.id), ticket);
      queryClient.invalidateQueries({
        queryKey: projectTicketsQueryKey(ticket.project_id),
      });
    },
  });
}

/** Request ticket reassignment for the current assigned worker. */
export function useCreateTicketAssignmentRequest(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketAssignmentRequestPayload) =>
      apiRequest<TicketAssignmentRequest>(
        `/api/v1/tickets/${ticketId}/assignment-requests`,
        {
          method: "POST",
          body: JSON.stringify(payload),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ticketAssignmentRequestsQueryKey(),
      });
    },
  });
}

/** Keep pending ticket handoff requests for the current worker in cache. */
export function useTicketAssignmentRequests() {
  return useQuery({
    queryKey: ticketAssignmentRequestsQueryKey(),
    queryFn: () =>
      apiRequest<TicketAssignmentRequestListResponse>(
        "/api/v1/ticket-assignment-requests?limit=100&offset=0",
      ),
    staleTime: ticketStaleTimeMs,
  });
}

/** Accept or decline a pending ticket handoff request. */
export function useResolveTicketAssignmentRequest(
  action: "accept" | "decline",
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (requestId: string) =>
      apiRequest<TicketAssignmentRequest>(
        `/api/v1/ticket-assignment-requests/${requestId}/${action}`,
        { method: "POST" },
      ),
    onSuccess: (request) => {
      queryClient.invalidateQueries({
        queryKey: ticketAssignmentRequestsQueryKey(),
      });
      queryClient.invalidateQueries({
        queryKey: ticketQueryKey(request.task_id),
      });
      queryClient.invalidateQueries({
        queryKey: projectTicketsQueryKey(request.project_id),
      });
    },
  });
}

/** Keep ticket comments in cache. */
export function useTicketComments(
  ticketId: string | undefined,
  client = false,
) {
  return useQuery({
    queryKey: ticketId
      ? [...ticketCommentsQueryKey(ticketId), client]
      : ["comments", "missing"],
    queryFn: () =>
      apiRequest<TicketCommentListResponse>(
        client
          ? `/api/v1/client/tickets/${ticketId}/comments?limit=100&offset=0`
          : `/api/v1/tickets/${ticketId}/comments?limit=100&offset=0`,
      ),
    enabled: Boolean(ticketId),
    staleTime: ticketStaleTimeMs,
  });
}

/** Add one ticket comment from either client or internal surfaces. */
export function useCreateTicketComment(ticketId: string, client = false) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      apiRequest<TicketComment>(
        client
          ? `/api/v1/client/tickets/${ticketId}/comments`
          : `/api/v1/tickets/${ticketId}/comments`,
        {
          method: "POST",
          body: JSON.stringify({ body }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ticketCommentsQueryKey(ticketId),
      });
    },
  });
}

/** Keep client-accessible projects in cache. */
export function useClientProjects() {
  return useQuery({
    queryKey: ["client", "projects"],
    queryFn: () =>
      apiRequest<ClientProjectListResponse>("/api/v1/client/projects"),
    staleTime: ticketStaleTimeMs,
  });
}

/** Create a ticket from the restricted client shell. */
export function useCreateClientTicket(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketPayload) =>
      apiRequest<Ticket>(`/api/v1/client/projects/${projectId}/tickets`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["client", "tickets"] });
    },
  });
}

/** Keep the client's own ticket list in cache. */
export function useClientTickets(pagination: PaginationParams) {
  return useQuery({
    queryKey: ["client", "tickets", pagination],
    queryFn: () =>
      apiRequest<TicketListResponse>(
        `/api/v1/client/tickets?${paginationSearchParams(pagination)}`,
      ),
    staleTime: ticketStaleTimeMs,
  });
}

/** Keep one client-owned ticket in cache. */
export function useClientTicket(ticketId: string | undefined) {
  return useQuery({
    queryKey: ticketId
      ? ["client", "tickets", ticketId]
      : ["client", "tickets", "missing"],
    queryFn: () => apiRequest<Ticket>(`/api/v1/client/tickets/${ticketId}`),
    enabled: Boolean(ticketId),
    staleTime: ticketStaleTimeMs,
  });
}

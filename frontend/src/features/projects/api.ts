// Project API helpers and React Query hooks for SPEC-106 screens.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import { PaginationParams } from "../organizations/types";
import {
  Project,
  ProjectListResponse,
  ProjectMembershipListResponse,
  ProjectPayload,
} from "./types";
import { Invitation } from "../organizations/types";

export const projectsRootQueryKey = ["projects"] as const;
const projectsStaleTimeMs = 30_000;

/** Build a stable query key for one organization's project list. */
export function organizationProjectsQueryKey(
  organizationId: string,
  pagination?: PaginationParams,
) {
  return ["organizations", organizationId, "projects", pagination] as const;
}

/** Build a stable query key for one project detail response. */
export function projectQueryKey(projectId: string) {
  return ["projects", projectId] as const;
}

/** Build a stable query key for one project's explicit member list. */
export function projectMembersQueryKey(projectId: string) {
  return ["projects", projectId, "members"] as const;
}

/** Convert pagination state into backend query parameters. */
function paginationSearchParams(pagination: PaginationParams) {
  const searchParams = new URLSearchParams({
    limit: String(pagination.limit),
    offset: String(pagination.offset),
  });
  return searchParams.toString();
}

/** Fetch one organization's projects using backend pagination. */
export function listOrganizationProjects(
  organizationId: string,
  pagination: PaginationParams,
) {
  return apiRequest<ProjectListResponse>(
    `/api/v1/organizations/${organizationId}/projects?${paginationSearchParams(
      pagination,
    )}`,
  );
}

/** Fetch one project by public UUID. */
export function getProject(projectId: string) {
  return apiRequest<Project>(`/api/v1/projects/${projectId}`);
}

/** Fetch explicit members for one project. */
export function listProjectMembers(projectId: string) {
  return apiRequest<ProjectMembershipListResponse>(
    `/api/v1/projects/${projectId}/members`,
  );
}

/** Keep one organization's project list in React Query cache. */
export function useOrganizationProjects(
  organizationId: string | undefined,
  pagination: PaginationParams,
) {
  return useQuery({
    queryKey: organizationId
      ? organizationProjectsQueryKey(organizationId, pagination)
      : ["organizations", "missing", "projects", pagination],
    queryFn: () => listOrganizationProjects(organizationId ?? "", pagination),
    enabled: Boolean(organizationId),
    staleTime: projectsStaleTimeMs,
  });
}

/** Keep one project detail response in React Query cache. */
export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: projectId ? projectQueryKey(projectId) : ["projects", "missing"],
    queryFn: () => getProject(projectId ?? ""),
    enabled: Boolean(projectId),
    staleTime: projectsStaleTimeMs,
  });
}

/** Keep explicit project members in React Query cache. */
export function useProjectMembers(projectId: string | undefined) {
  return useQuery({
    queryKey: projectId
      ? projectMembersQueryKey(projectId)
      : ["projects", "missing", "members"],
    queryFn: () => listProjectMembers(projectId ?? ""),
    enabled: Boolean(projectId),
    staleTime: projectsStaleTimeMs,
  });
}

/** Create a project and refresh organization-level project state. */
export function useCreateProject(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectPayload) =>
      apiRequest<Project>(`/api/v1/organizations/${organizationId}/projects`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({
        queryKey: ["organizations", organizationId, "projects"],
      });
      queryClient.setQueryData(projectQueryKey(project.id), project);
    },
  });
}

/** Update project metadata or archive state and refresh dependent cache. */
export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProjectPayload) =>
      apiRequest<Project>(`/api/v1/projects/${projectId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({
        queryKey: ["organizations", project.organization_id, "projects"],
      });
      queryClient.setQueryData(projectQueryKey(project.id), project);
    },
  });
}

/** Invite an organization member to join a project. */
export function useCreateProjectInvitation(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      apiRequest<Invitation>(`/api/v1/projects/${projectId}/invitations`, {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: projectMembersQueryKey(projectId),
      });
    },
  });
}

/** Remove explicit membership from a project. */
export function useRemoveProjectMember(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      apiRequest<undefined>(`/api/v1/projects/${projectId}/members/${userId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: projectMembersQueryKey(projectId),
      });
    },
  });
}

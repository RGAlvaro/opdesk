// Organization API helpers and React Query hooks for SPEC-105 screens.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import {
  MembershipListResponse,
  Organization,
  OrganizationListResponse,
  OrganizationRole,
} from "./types";

export const organizationsQueryKey = ["organizations"] as const;
const organizationStaleTimeMs = 30_000;

/** Build a stable query key for one organization detail response. */
export function organizationQueryKey(organizationId: string) {
  return ["organizations", organizationId] as const;
}

/** Build a stable query key for one organization's member list. */
export function organizationMembersQueryKey(organizationId: string) {
  return ["organizations", organizationId, "members"] as const;
}

/** Fetch organizations visible to the authenticated user. */
export function listOrganizations() {
  return apiRequest<OrganizationListResponse>("/api/v1/organizations");
}

/** Fetch one organization by public UUID. */
export function getOrganization(organizationId: string) {
  return apiRequest<Organization>(`/api/v1/organizations/${organizationId}`);
}

/** Fetch administrator-visible memberships for one organization. */
export function listOrganizationMembers(organizationId: string) {
  return apiRequest<MembershipListResponse>(
    `/api/v1/organizations/${organizationId}/members`,
  );
}

/** Keep the current user's organization list in React Query cache. */
export function useOrganizations() {
  return useQuery({
    queryKey: organizationsQueryKey,
    queryFn: listOrganizations,
    staleTime: organizationStaleTimeMs,
  });
}

/** Keep one organization detail response in React Query cache. */
export function useOrganization(organizationId: string | undefined) {
  return useQuery({
    queryKey: organizationId
      ? organizationQueryKey(organizationId)
      : ["organizations", "missing"],
    queryFn: () => getOrganization(organizationId ?? ""),
    enabled: Boolean(organizationId),
    staleTime: organizationStaleTimeMs,
  });
}

/** Keep one organization member list in React Query cache. */
export function useOrganizationMembers(
  organizationId: string | undefined,
  enabled: boolean,
) {
  return useQuery({
    queryKey: organizationId
      ? organizationMembersQueryKey(organizationId)
      : ["organizations", "missing", "members"],
    queryFn: () => listOrganizationMembers(organizationId ?? ""),
    enabled: Boolean(organizationId) && enabled,
    staleTime: organizationStaleTimeMs,
  });
}

/** Create an organization and refresh list-level cache. */
export function useCreateOrganization() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name: string; slug?: string }) =>
      apiRequest<Organization>("/api/v1/organizations", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (organization) => {
      queryClient.invalidateQueries({ queryKey: organizationsQueryKey });
      queryClient.setQueryData(
        organizationQueryKey(organization.id),
        organization,
      );
    },
  });
}

/** Update organization settings and refresh dependent cache entries. */
export function useUpdateOrganization(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { name?: string; slug?: string }) =>
      apiRequest<Organization>(`/api/v1/organizations/${organizationId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: (organization) => {
      queryClient.invalidateQueries({ queryKey: organizationsQueryKey });
      queryClient.setQueryData(
        organizationQueryKey(organization.id),
        organization,
      );
    },
  });
}

/** Permanently delete an organization and clear stale organization cache. */
export function useDeleteOrganization(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<undefined>(`/api/v1/organizations/${organizationId}`, {
        method: "DELETE",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: organizationsQueryKey });
      queryClient.removeQueries({
        queryKey: organizationQueryKey(organizationId),
      });
      queryClient.removeQueries({
        queryKey: organizationMembersQueryKey(organizationId),
      });
    },
  });
}

/** Change a non-owner member between admin and member roles. */
export function useUpdateMemberRole(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      userId: string;
      role: Exclude<OrganizationRole, "owner">;
    }) =>
      apiRequest(
        `/api/v1/organizations/${organizationId}/members/${payload.userId}`,
        {
          method: "PATCH",
          body: JSON.stringify({ role: payload.role }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: organizationMembersQueryKey(organizationId),
      });
    },
  });
}

/** Remove a non-owner member from an organization. */
export function useRemoveMember(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) =>
      apiRequest<undefined>(
        `/api/v1/organizations/${organizationId}/members/${userId}`,
        { method: "DELETE" },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: organizationMembersQueryKey(organizationId),
      });
    },
  });
}

/** Transfer ownership to another existing organization member. */
export function useTransferOwnership(organizationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (newOwnerUserId: string) =>
      apiRequest<undefined>(
        `/api/v1/organizations/${organizationId}/transfer-ownership`,
        {
          method: "POST",
          body: JSON.stringify({ new_owner_user_id: newOwnerUserId }),
        },
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: organizationQueryKey(organizationId),
      });
      queryClient.invalidateQueries({
        queryKey: organizationMembersQueryKey(organizationId),
      });
      queryClient.invalidateQueries({ queryKey: organizationsQueryKey });
    },
  });
}

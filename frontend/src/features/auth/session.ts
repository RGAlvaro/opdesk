// React Query session and auth mutations for cookie-backed authentication.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import { LoginResponse, StatusResponse, User } from "./types";

export const sessionQueryKey = ["session"];

/** Load the current authenticated user from the profile endpoint. */
export function fetchCurrentUser() {
  return apiRequest<User>("/api/v1/users/me");
}

/** Keep the current session user available to guards and app chrome. */
export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: fetchCurrentUser,
    staleTime: 30_000,
  });
}

/** Authenticate credentials and seed the session cache with the returned user. */
export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: { email: string; password: string }) =>
      apiRequest<LoginResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (response) => {
      queryClient.setQueryData(sessionQueryKey, response.user);
    },
  });
}

/** Register a new account, log it in, and seed the session cache. */
export function useSignup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      email: string;
      password: string;
      full_name: string;
    }) => {
      await apiRequest<User>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      const loginResponse = await apiRequest<LoginResponse>(
        "/api/v1/auth/login",
        {
          method: "POST",
          body: JSON.stringify({
            email: payload.email,
            password: payload.password,
          }),
        },
      );
      return loginResponse.user;
    },
    onSuccess: (user) => {
      queryClient.setQueryData(sessionQueryKey, user);
    },
  });
}

/** Clear the server session cookies and remove cached user state. */
export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiRequest<StatusResponse | undefined>("/api/v1/auth/logout", {
        method: "POST",
      }),
    onSettled: async () => {
      await queryClient.cancelQueries({ queryKey: sessionQueryKey });
      queryClient.removeQueries({ queryKey: sessionQueryKey });
    },
  });
}

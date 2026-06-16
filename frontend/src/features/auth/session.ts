import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import { LoginResponse, StatusResponse, User } from "./types";

export const sessionQueryKey = ["session"];

export function fetchCurrentUser() {
  return apiRequest<User>("/api/v1/users/me");
}

export function useSession() {
  return useQuery({
    queryKey: sessionQueryKey,
    queryFn: fetchCurrentUser,
    staleTime: 30_000,
  });
}

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

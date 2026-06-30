// Task API helpers and React Query hooks for SPEC-106 screens.

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiRequest } from "../../shared/api";
import { PaginationParams } from "../organizations/types";
import { projectQueryKey } from "../projects/api";
import { Task, TaskFilters, TaskListResponse, TaskPayload } from "./types";

const tasksStaleTimeMs = 30_000;

/** Build a stable query key for one project's filtered task list. */
export function projectTasksQueryKey(
  projectId: string,
  filters: TaskFilters,
  pagination: PaginationParams,
) {
  return ["projects", projectId, "tasks", filters, pagination] as const;
}

/** Build a stable prefix for every task list under one project. */
export function projectTasksPrefixQueryKey(projectId: string) {
  return ["projects", projectId, "tasks"] as const;
}

/** Build a stable query key for one task detail response. */
export function taskQueryKey(taskId: string) {
  return ["tasks", taskId] as const;
}

/** Convert task filters and pagination into backend query parameters. */
function taskSearchParams(filters: TaskFilters, pagination: PaginationParams) {
  const searchParams = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      searchParams.set(key, value);
    }
  });
  searchParams.set("limit", String(pagination.limit));
  searchParams.set("offset", String(pagination.offset));
  const query = searchParams.toString();
  return query ? `?${query}` : "";
}

/** Fetch one project's tasks using optional backend filters and pagination. */
export function listProjectTasks(
  projectId: string,
  filters: TaskFilters,
  pagination: PaginationParams,
) {
  return apiRequest<TaskListResponse>(
    `/api/v1/projects/${projectId}/tasks${taskSearchParams(
      filters,
      pagination,
    )}`,
  );
}

/** Fetch one task by public UUID. */
export function getTask(taskId: string) {
  return apiRequest<Task>(`/api/v1/tasks/${taskId}`);
}

/** Keep one project's filtered task list in React Query cache. */
export function useProjectTasks(
  projectId: string | undefined,
  filters: TaskFilters,
  pagination: PaginationParams,
) {
  return useQuery({
    queryKey: projectId
      ? projectTasksQueryKey(projectId, filters, pagination)
      : ["projects", "missing", "tasks", filters, pagination],
    queryFn: () => listProjectTasks(projectId ?? "", filters, pagination),
    enabled: Boolean(projectId),
    staleTime: tasksStaleTimeMs,
  });
}

/** Keep one task detail response in React Query cache. */
export function useTask(taskId: string | undefined) {
  return useQuery({
    queryKey: taskId ? taskQueryKey(taskId) : ["tasks", "missing"],
    queryFn: () => getTask(taskId ?? ""),
    enabled: Boolean(taskId),
    staleTime: tasksStaleTimeMs,
  });
}

/** Create a task and refresh project task lists. */
export function useCreateTask(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TaskPayload) =>
      apiRequest<Task>(`/api/v1/projects/${projectId}/tasks`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onSuccess: (task) => {
      queryClient.invalidateQueries({
        queryKey: projectTasksPrefixQueryKey(projectId),
      });
      queryClient.setQueryData(taskQueryKey(task.id), task);
    },
  });
}

/** Update a task and refresh detail and related project list caches. */
export function useUpdateTask(taskId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TaskPayload) =>
      apiRequest<Task>(`/api/v1/tasks/${taskId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    onSuccess: (task) => {
      queryClient.invalidateQueries({
        queryKey: projectTasksPrefixQueryKey(task.project_id),
      });
      queryClient.invalidateQueries({
        queryKey: projectQueryKey(task.project_id),
      });
      queryClient.setQueryData(taskQueryKey(task.id), task);
    },
  });
}

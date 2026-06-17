// Shared browser API client that preserves cookie auth and normalizes errors.

/** Error envelope shape returned by the backend API convention. */
export type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
  };
};

/** Client-side representation of a backend API error response. */
export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;

  /** Preserve backend status, code, and details for UI-specific handling. */
  constructor(
    status: number,
    code: string,
    message: string,
    details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

/** Send a JSON API request with browser credentials and typed response data. */
export async function apiRequest<TResponse>(
  path: string,
  options: RequestInit = {},
): Promise<TResponse> {
  const response = await fetch(path, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (response.status === 204) {
    return undefined as TResponse;
  }

  const body = (await response.json().catch(() => ({}))) as
    | ApiErrorBody
    | TResponse;

  if (!response.ok) {
    const errorBody = body as ApiErrorBody;
    throw new ApiError(
      response.status,
      errorBody.error?.code ?? "unexpected_error",
      errorBody.error?.message ?? "Something went wrong.",
      errorBody.error?.details ?? {},
    );
  }

  return body as TResponse;
}

/** Return safe user-facing copy for known API errors and unknown failures. */
export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

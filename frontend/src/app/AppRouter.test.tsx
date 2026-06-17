// Frontend route and auth-flow tests for SPEC-104.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppRouter } from "./AppRouter";

const user = {
  id: "8847c8bf-2dd2-48f7-a3d1-5b1008700e4e",
  email: "user@example.com",
  full_name: "User Name",
  is_active: true,
  is_superuser: false,
  created_at: "2026-06-15T10:00:00Z",
  updated_at: "2026-06-15T10:00:00Z",
};

/** Build a JSON fetch response for mocked backend calls. */
function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Build an empty fetch response for endpoints like logout. */
function emptyResponse(status = 204) {
  return new Response(null, { status });
}

/** Build a backend-shaped API error response for UI assertions. */
function apiError(code: string, message: string, status: number) {
  return jsonResponse(
    {
      error: {
        code,
        message,
        details: {},
      },
    },
    status,
  );
}

/** Render the router under test with isolated query and memory-router state. */
function renderRoute(initialPath: string) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });

  /** Provide test-only routing and query context around the app router. */
  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[initialPath]}>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  }

  return render(<AppRouter />, { wrapper: Wrapper });
}

/** Queue deterministic fetch responses for a test case. */
function mockFetch(...responses: Response[]) {
  const fetchMock = vi.fn();
  responses.forEach((response) => fetchMock.mockResolvedValueOnce(response));
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SPEC-104 frontend app shell and auth UI", () => {
  it("renders the landing page with login and signup actions", async () => {
    mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
    );

    renderRoute("/");

    expect(
      await screen.findByRole("heading", {
        name: /operational work management/i,
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /log in/i })).toHaveAttribute(
      "href",
      "/login",
    );
    expect(
      screen.getByRole("link", { name: /create account/i }),
    ).toHaveAttribute("href", "/signup");
  });

  it("redirects authenticated visitors away from public routes", async () => {
    mockFetch(jsonResponse(user));

    renderRoute("/login");

    expect(
      await screen.findByRole("heading", { name: /workspace overview/i }),
    ).toBeInTheDocument();
  });

  it("validates the login form and renders safe failed-login errors", async () => {
    const fetchMock = mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
      apiError("invalid_credentials", "Invalid email or password.", 401),
    );
    const actor = userEvent.setup();

    renderRoute("/login");

    await screen.findByRole("heading", { name: "Log in" });
    await actor.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByText("Enter a valid email.")).toBeInTheDocument();
    expect(screen.getByText("Password is required.")).toBeInTheDocument();

    await actor.type(screen.getByLabelText("Email"), "missing@example.com");
    await actor.type(screen.getByLabelText("Password"), "Wrong1234");
    await actor.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid email or password.",
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
  });

  it("logs in successfully and renders the authenticated app shell", async () => {
    mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
      jsonResponse({ user }),
      jsonResponse(user),
    );
    const actor = userEvent.setup();

    renderRoute("/login");

    await actor.type(await screen.findByLabelText("Email"), "user@example.com");
    await actor.type(screen.getByLabelText("Password"), "Example1234");
    await actor.click(screen.getByRole("button", { name: "Log in" }));

    expect(
      await screen.findByRole("heading", { name: /workspace overview/i }),
    ).toBeInTheDocument();
    expect(screen.getByText("user@example.com")).toBeInTheDocument();
  });

  it("validates weak signup passwords before submission", async () => {
    const fetchMock = mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
    );
    const actor = userEvent.setup();

    renderRoute("/signup");

    await actor.type(await screen.findByLabelText("Full name"), "User Name");
    await actor.type(screen.getByLabelText("Email"), "user@example.com");
    await actor.type(screen.getByLabelText("Password"), "weak");
    await actor.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByText("Password must be at least 10 characters."),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("signs up, logs in, and reaches the app without exposing tokens", async () => {
    const fetchMock = mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
      jsonResponse(user, 201),
      jsonResponse({ user }),
      jsonResponse(user),
    );
    const actor = userEvent.setup();

    renderRoute("/signup");

    await actor.type(await screen.findByLabelText("Full name"), "User Name");
    await actor.type(screen.getByLabelText("Email"), "user@example.com");
    await actor.type(screen.getByLabelText("Password"), "Example1234");
    await actor.click(screen.getByRole("button", { name: "Create account" }));

    expect(
      await screen.findByRole("heading", { name: /workspace overview/i }),
    ).toBeInTheDocument();
    expect(screen.queryByText(/token/i)).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/register",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/auth/login",
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
  });

  it("redirects protected routes when unauthenticated", async () => {
    mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
    );

    renderRoute("/app/profile");

    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });

  it("renders session shell and keeps future navigation unavailable", async () => {
    mockFetch(jsonResponse(user));

    renderRoute("/app");

    expect(
      await screen.findByRole("heading", { name: /workspace overview/i }),
    ).toBeInTheDocument();

    const nav = screen.getByRole("navigation", { name: /primary navigation/i });
    expect(within(nav).getByText("Organizations")).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(within(nav).getByText("Projects")).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    expect(within(nav).getByText("Tasks")).toHaveAttribute(
      "aria-disabled",
      "true",
    );
  });

  it("logs out and returns to the landing page", async () => {
    mockFetch(
      jsonResponse(user),
      emptyResponse(),
      apiError("not_authenticated", "Authentication is required.", 401),
    );
    const actor = userEvent.setup();

    renderRoute("/app");

    await screen.findByRole("heading", { name: /workspace overview/i });
    await actor.click(screen.getByRole("button", { name: "Sign out" }));

    expect(
      await screen.findByRole("heading", {
        name: /operational work management/i,
      }),
    ).toBeInTheDocument();
  });

  it("loads and updates the profile", async () => {
    const updatedUser = { ...user, full_name: "Updated Name" };
    mockFetch(jsonResponse(user), jsonResponse(updatedUser));
    const actor = userEvent.setup();

    renderRoute("/app/profile");

    expect(
      await screen.findByRole("heading", { name: "Profile" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText("user@example.com")).toHaveLength(2);

    const fullName = screen.getByLabelText("Full name");
    await actor.clear(fullName);
    await actor.type(fullName, "Updated Name");
    await actor.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Profile updated.",
    );
    await waitFor(() =>
      expect(screen.getByDisplayValue("Updated Name")).toBeInTheDocument(),
    );
  });

  it("renders invalid profile server errors", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("invalid_profile", "Full name is required.", 400),
    );
    const actor = userEvent.setup();

    renderRoute("/app/profile");

    const fullName = await screen.findByLabelText("Full name");
    await actor.clear(fullName);
    await actor.type(fullName, "Rejected Name");
    await actor.click(screen.getByRole("button", { name: "Save changes" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Full name is required.",
    );
  });

  it("redirects to login when profile update loses authentication", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("not_authenticated", "Authentication is required.", 401),
      apiError("not_authenticated", "Authentication is required.", 401),
    );
    const actor = userEvent.setup();

    renderRoute("/app/profile");

    const fullName = await screen.findByLabelText("Full name");
    await actor.clear(fullName);
    await actor.type(fullName, "Updated Name");
    await actor.click(screen.getByRole("button", { name: "Save changes" }));

    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });
});

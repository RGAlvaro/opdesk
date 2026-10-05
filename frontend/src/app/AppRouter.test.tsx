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
  job_title: null,
  phone: null,
  timezone: null,
  locale: null,
  avatar_url: null,
  bio: null,
  is_active: true,
  is_superuser: false,
  account_type: "internal",
  created_at: "2026-06-15T10:00:00Z",
  updated_at: "2026-06-15T10:00:00Z",
};

const clientUser = {
  ...user,
  id: "c395a77f-9f47-4f66-aa91-d7f5c06b0cbd",
  email: "client@example.com",
  full_name: "Client User",
  account_type: "client",
};

const organization = {
  id: "9ed75133-2898-4d82-8d1c-0da379207144",
  name: "Acme Ops",
  slug: "acme-ops",
  role: "owner",
  created_at: "2026-06-20T10:00:00Z",
  updated_at: "2026-06-20T10:00:00Z",
};

const project = {
  id: "68163673-46be-4baa-97ec-9138258c6b7d",
  organization_id: organization.id,
  name: "Customer Onboarding",
  description: "Implementation work",
  is_archived: false,
  status: "active",
  start_date: "2026-06-21",
  end_date: "2026-07-21",
  budget_amount: "1200.00",
  budget_currency: "EUR",
  visibility: "organization",
  project_owner_id: user.id,
  created_at: "2026-06-21T10:00:00Z",
  updated_at: "2026-06-21T10:00:00Z",
};

const worker = {
  id: "cf5965d5-b300-41e6-9a5a-00304f9cdab8",
  email: "worker@example.com",
  full_name: "Worker User",
  account_type: "internal",
};

const ticket = {
  id: "a2ca8f75-95af-43a6-bb8c-90d0baec8dc0",
  organization_id: organization.id,
  project_id: project.id,
  title: "Printer down",
  description: "The printer is offline.",
  status: "todo",
  priority: "medium",
  assignee_id: worker.id,
  client_user_id: clientUser.id,
  task_type: "ticket",
  created_at: "2026-06-21T12:00:00Z",
  updated_at: "2026-06-21T12:30:00Z",
};

const clientAccess = {
  id: "88a6b1b4-4d98-4723-aa63-b005404d7784",
  organization_id: organization.id,
  project_id: project.id,
  client_user_id: clientUser.id,
  granted_by_id: user.id,
  revoked_at: null,
  client: clientUser,
  created_at: "2026-06-21T11:00:00Z",
};

const assignmentRequest = {
  id: "a37ad584-4016-47ac-b33e-bac226212a7c",
  task_id: ticket.id,
  organization_id: organization.id,
  project_id: project.id,
  requested_by_id: user.id,
  target_user_id: worker.id,
  status: "pending",
  ticket,
  created_at: "2026-06-21T12:45:00Z",
  responded_at: null,
};

const auditRun = {
  id: "bf464c94-e5fc-4911-a4ac-ed08b2b9ed30",
  job_name: "external_delivery_retry_sweep",
  scheduled_for: null,
  started_at: "2026-09-15T09:00:00Z",
  finished_at: "2026-09-15T09:00:03Z",
  status: "succeeded",
  records_seen: 4,
  records_changed: 2,
  error_code: null,
  error_message: null,
  created_at: "2026-09-15T09:00:00Z",
  updated_at: "2026-09-15T09:00:03Z",
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

/** Build a paginated API response for list-route assertions. */
function page<TItem>(items: TItem[]) {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
  };
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
  const queuedResponses = [...responses];
  const fetchMock = vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/v1/notifications/unread-count")) {
      return Promise.resolve(jsonResponse({ unread_count: 0 }));
    }
    if (url.includes("/api/v1/notifications")) {
      return Promise.resolve(jsonResponse(page([])));
    }
    if (url.endsWith("/api/v1/organizations")) {
      return Promise.resolve(jsonResponse(page([organization])));
    }
    if (url.includes("/api/v1/client/projects")) {
      return Promise.resolve(jsonResponse({ items: [project] }));
    }
    if (url.includes("/api/v1/client/tickets")) {
      return Promise.resolve(jsonResponse(page([])));
    }
    if (url.includes(`/api/v1/projects/${project.id}/members`)) {
      return Promise.resolve(jsonResponse(page([])));
    }
    if (url.includes(`/api/v1/projects/${project.id}/labels`)) {
      return Promise.resolve(jsonResponse(page([])));
    }
    if (url.includes(`/api/v1/projects/${project.id}/clients`)) {
      return Promise.resolve(jsonResponse(page([])));
    }
    if (url.includes(`/api/v1/projects/${project.id}/tasks`)) {
      return Promise.resolve(jsonResponse(page([])));
    }
    const nextResponse = queuedResponses.shift();
    if (nextResponse) {
      return Promise.resolve(nextResponse);
    }
    return Promise.resolve(
      apiError("unexpected_error", "Unexpected request.", 500),
    );
  });
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
  it("renders the SPEC-318 portfolio sections and public links", async () => {
    const fetchMock = mockFetch();

    renderRoute("/");

    expect(
      await screen.findByRole("heading", {
        name: "Selected work",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText(/software engineer/i)).toBeInTheDocument();
    expect(
      screen.queryByText(/ideas · tools · better days/i),
    ).not.toBeInTheDocument();
    const opsDesk = screen.getByRole("region", { name: "OpsDesk" });
    const approach = screen.getByRole("region", { name: "My approach" });
    const eventflow = screen.getByRole("region", { name: "EventFlow" });
    expect(within(opsDesk).getByText("Available")).toBeInTheDocument();
    expect(
      within(opsDesk).getByRole("link", { name: /open opsdesk/i }),
    ).toHaveAttribute("href", "/login");
    expect(
      within(opsDesk).getByRole("link", { name: /create account/i }),
    ).toHaveAttribute("href", "/signup");
    expect(
      within(approach)
        .getAllByRole("heading", { level: 3 })
        .map((heading) => heading.textContent),
    ).toEqual(["Spec", "Build", "Validate", "Release"]);
    expect(within(eventflow).getByText("Code available")).toBeInTheDocument();
    expect(
      within(eventflow).getByText(
        /durable event ingestion and signed webhook delivery/i,
      ),
    ).toBeInTheDocument();
    expect(
      within(eventflow).getByText(/still in development/i),
    ).toBeInTheDocument();
    expect(
      within(eventflow).getByRole("link", { name: /view repository/i }),
    ).toHaveAttribute("href", "https://github.com/RGAlvaro/eventflow");
    expect(
      opsDesk.compareDocumentPosition(approach) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      approach.compareDocumentPosition(eventflow) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getAllByText("Available")).toHaveLength(1);
    expect(screen.queryByText("Coming soon")).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /changelog|release notes/i })[0],
    ).toHaveAttribute("href", "/changelog");
    expect(screen.getByRole("link", { name: "Terms" })).toHaveAttribute(
      "href",
      "/terms",
    );
    expect(screen.getByRole("link", { name: "Copyright" })).toHaveAttribute(
      "href",
      "/copyright",
    );
    expect(screen.getByRole("link", { name: "Cookies" })).toHaveAttribute(
      "href",
      "/cookies",
    );
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders project client management in project settings", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(user));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.includes(`/api/v1/projects/${project.id}/clients`)) {
          return Promise.resolve(jsonResponse(page([clientAccess])));
        }
        if (url.includes(`/api/v1/organizations/${organization.id}/members`)) {
          return Promise.resolve(jsonResponse(page([])));
        }
        if (url.includes(`/api/v1/organizations/${organization.id}`)) {
          return Promise.resolve(jsonResponse(organization));
        }
        if (url.includes(`/api/v1/projects/${project.id}`)) {
          return Promise.resolve(jsonResponse(project));
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );

    renderRoute(`/app/projects/${project.id}/settings`);

    expect(
      await screen.findByRole("heading", { name: "Project clients" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("Client User")).toBeInTheDocument();
    expect(screen.getByText("client@example.com")).toBeInTheDocument();
  });

  it("lets a client create a ticket from the restricted shell", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(clientUser));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.includes("/api/v1/client/projects")) {
          return Promise.resolve(jsonResponse({ items: [project] }));
        }
        if (
          url.includes(`/api/v1/client/projects/${project.id}/tickets`) &&
          init?.method === "POST"
        ) {
          return Promise.resolve(jsonResponse(ticket, 201));
        }
        if (url.includes("/api/v1/client/tickets")) {
          return Promise.resolve(jsonResponse(page([])));
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );
    const actor = userEvent.setup();

    renderRoute("/app/client");

    await screen.findByRole("heading", { name: "My tickets" });
    await actor.selectOptions(screen.getByLabelText("Project"), project.id);
    await actor.type(screen.getByLabelText("Subject"), "Printer down");
    await actor.type(screen.getByLabelText("Description"), "Offline.");
    await actor.click(screen.getByRole("button", { name: /create ticket/i }));

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/v1/client/projects/${project.id}/tickets`,
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });

  it("renders client ticket detail comments and safe assignment state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(clientUser));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.includes(`/api/v1/client/tickets/${ticket.id}/comments`)) {
          if (init?.method === "POST") {
            return Promise.resolve(
              jsonResponse(
                {
                  id: "78076d2d-cc2f-4282-9a2c-68f65808357b",
                  task_id: ticket.id,
                  organization_id: organization.id,
                  project_id: project.id,
                  author_user_id: clientUser.id,
                  body: "Any update?",
                  created_at: "2026-06-21T13:00:00Z",
                  updated_at: "2026-06-21T13:00:00Z",
                },
                201,
              ),
            );
          }
          return Promise.resolve(jsonResponse(page([])));
        }
        if (url.includes(`/api/v1/client/tickets/${ticket.id}`)) {
          return Promise.resolve(jsonResponse(ticket));
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/client/tickets/${ticket.id}`);

    expect(await screen.findByText("Assigned")).toBeInTheDocument();
    await actor.type(screen.getByRole("textbox"), "Any update?");
    await actor.click(screen.getByRole("button", { name: /add comment/i }));

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/v1/client/tickets/${ticket.id}/comments`,
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });

  it("shows internal ticket visibility and assignment request controls", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(user));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.includes(`/api/v1/projects/${project.id}/members`)) {
          return Promise.resolve(
            jsonResponse(page([{ user_id: worker.id, user: worker }])),
          );
        }
        if (url.includes(`/api/v1/projects/${project.id}/tickets`)) {
          return Promise.resolve(jsonResponse(page([ticket])));
        }
        if (url.includes(`/api/v1/projects/${project.id}`)) {
          return Promise.resolve(jsonResponse(project));
        }
        if (url.includes(`/api/v1/tickets/${ticket.id}/comments`)) {
          return Promise.resolve(jsonResponse(page([])));
        }
        if (url.includes(`/api/v1/tickets/${ticket.id}`)) {
          return Promise.resolve(jsonResponse(ticket));
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );

    renderRoute(`/app/tickets/${ticket.id}`);

    expect(await screen.findAllByText("Worker User")).toHaveLength(2);
    expect(
      screen.getByRole("heading", { name: "Request reassignment" }),
    ).toBeInTheDocument();
  });

  it("lets an internal worker accept a pending ticket assignment request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(user));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.includes("/api/v1/ticket-assignment-requests")) {
          if (init?.method === "POST") {
            return Promise.resolve(
              jsonResponse({ ...assignmentRequest, status: "accepted" }),
            );
          }
          return Promise.resolve(jsonResponse(page([assignmentRequest])));
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );
    const actor = userEvent.setup();

    renderRoute("/app/ticket-assignment-requests");

    expect(
      await screen.findByRole("heading", { name: "Assignment requests" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Printer down")).toBeInTheDocument();
    await actor.click(screen.getByRole("button", { name: "Accept" }));

    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        `/api/v1/ticket-assignment-requests/${assignmentRequest.id}/accept`,
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });

  it("shows operational audit navigation and filters for owner/admin users", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(user));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.endsWith("/api/v1/organizations")) {
          return Promise.resolve(jsonResponse(page([organization])));
        }
        if (url.includes("/api/v1/admin/operational-audit")) {
          return Promise.resolve(jsonResponse(page([auditRun])));
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );
    const actor = userEvent.setup();

    renderRoute("/app/admin/operational-audit");

    expect(
      await screen.findByRole("link", { name: /operational audit/i }),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("heading", { name: "Operational audit" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("external_delivery_retry_sweep"),
    ).toBeInTheDocument();
    await actor.selectOptions(screen.getByLabelText("Status"), "succeeded");
    await actor.click(screen.getByRole("button", { name: /filter/i }));

    await waitFor(() =>
      expect(
        vi
          .mocked(fetch)
          .mock.calls.some(([url]) => String(url).includes("status=succeeded")),
      ).toBe(true),
    );
  });

  it("hides operational audit navigation and renders API denial for members", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/v1/users/me")) {
          return Promise.resolve(jsonResponse(user));
        }
        if (url.includes("/api/v1/notifications/unread-count")) {
          return Promise.resolve(jsonResponse({ unread_count: 0 }));
        }
        if (url.endsWith("/api/v1/organizations")) {
          return Promise.resolve(
            jsonResponse(page([{ ...organization, role: "member" }])),
          );
        }
        if (url.includes("/api/v1/admin/operational-audit")) {
          return Promise.resolve(
            apiError(
              "insufficient_role",
              "Your organization role is insufficient.",
              403,
            ),
          );
        }
        return Promise.resolve(jsonResponse(page([])));
      }),
    );

    renderRoute("/app/admin/operational-audit");

    expect(
      await screen.findByRole("heading", { name: "Operational audit" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: /operational audit/i }),
    ).not.toBeInTheDocument();
    expect(
      await screen.findByText("Your organization role is insufficient."),
    ).toBeInTheDocument();
  });

  it("shows EventFlow's current backend work without a fake app link", async () => {
    mockFetch();

    renderRoute("/");

    const eventflowCard = await screen.findByRole("region", {
      name: "EventFlow",
    });
    expect(
      within(eventflowCard).getByText("Code available"),
    ).toBeInTheDocument();
    expect(
      within(eventflowCard).getByText("Backend project"),
    ).toBeInTheDocument();
    expect(
      within(eventflowCard).getByText(
        /interface and live demo are still in development/i,
      ),
    ).toBeInTheDocument();
    expect(within(eventflowCard).getAllByRole("link")).toHaveLength(1);
    expect(
      eventflowCard.querySelector("img.portfolio-next__art"),
    ).toHaveAttribute("alt", "");
    expect(
      within(eventflowCard).getByRole("link", { name: /view repository/i }),
    ).toHaveAttribute("href", "https://github.com/RGAlvaro/eventflow");
  });

  it("renders the public changelog without authentication", async () => {
    const fetchMock = mockFetch();

    renderRoute("/changelog");

    expect(
      await screen.findByRole("heading", { name: "Changelog" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "2026-08-18 - Collaboration Release",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", {
        name: "2026-08-14 - Notification Inbox Release",
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/internal team members can use organization chat/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/persistent in-app notification inbox/i),
    ).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it.each([
    ["/terms", "Terminos y condiciones", /plantilla informativa/i],
    ["/copyright", "Copyright", /todos los derechos reservados/i],
    ["/cookies", "Politica de cookies", /access_token/i],
  ])(
    "renders public legal page %s without authentication",
    async (path, heading, expectedText) => {
      const fetchMock = mockFetch();

      renderRoute(path);

      expect(
        await screen.findByRole("heading", { name: heading }),
      ).toBeInTheDocument();
      expect(screen.getByText(expectedText)).toBeInTheDocument();
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );

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

  it("renders session shell with safe no-context project and task navigation", async () => {
    mockFetch(jsonResponse(user));

    renderRoute("/app");

    expect(
      await screen.findByRole("heading", { name: /workspace overview/i }),
    ).toBeInTheDocument();

    const nav = screen.getByRole("navigation", { name: /primary navigation/i });
    expect(
      within(nav).getByRole("link", { name: /organizations/i }),
    ).toHaveAttribute("href", "/app/organizations");
    expect(
      within(nav).getByRole("button", { name: /projects/i }),
    ).toBeDisabled();
    expect(within(nav).getByRole("button", { name: /tasks/i })).toBeDisabled();
  });

  it("keeps Organizations active by itself after opening the nav item", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(organization),
      jsonResponse(page([organization])),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${organization.id}`);

    const nav = await screen.findByRole("navigation", {
      name: /primary navigation/i,
    });
    expect(
      within(nav).getByRole("link", { name: /organizations/i }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(nav).getByRole("link", { name: /projects/i }),
    ).not.toHaveAttribute("aria-current");

    await actor.click(
      within(nav).getByRole("link", { name: /organizations/i }),
    );

    expect(
      await screen.findByRole("heading", { name: "Organizations" }),
    ).toBeInTheDocument();
    expect(
      within(nav).getByRole("link", { name: /organizations/i }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(nav).getByRole("button", { name: /projects/i }),
    ).toBeDisabled();
    expect(
      within(nav).getByRole("button", { name: /tasks/i }),
    ).not.toHaveAttribute("aria-current");
  });

  it("routes Projects to the active organization and marks only Projects active", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(organization),
      jsonResponse(page([])),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${organization.id}`);

    const nav = await screen.findByRole("navigation", {
      name: /primary navigation/i,
    });
    await actor.click(within(nav).getByRole("link", { name: /projects/i }));

    expect(
      await screen.findByRole("heading", { name: "Projects" }),
    ).toBeInTheDocument();
    expect(
      within(nav).getByRole("link", { name: /projects/i }),
    ).toHaveAttribute("href", `/app/organizations/${organization.id}/projects`);
    expect(
      within(nav).getByRole("link", { name: /projects/i }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(nav).getByRole("link", { name: /organizations/i }),
    ).not.toHaveAttribute("aria-current");
    expect(
      within(nav).getByRole("button", { name: /tasks/i }),
    ).not.toHaveAttribute("aria-current");
  });

  it("routes Tasks to the current project task list and marks only Tasks active", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(organization),
      jsonResponse(page([])),
      jsonResponse(page([])),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/projects/${project.id}`);

    expect(
      await screen.findByRole("heading", { name: project.name }),
    ).toBeInTheDocument();

    const nav = await screen.findByRole("navigation", {
      name: /primary navigation/i,
    });
    expect(
      within(nav).getByRole("link", { name: /projects/i }),
    ).toHaveAttribute("href", `/app/organizations/${organization.id}/projects`);
    expect(
      within(nav).getByRole("link", { name: /projects/i }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(nav).getByRole("link", { name: /organizations/i }),
    ).not.toHaveAttribute("aria-current");

    await actor.click(within(nav).getByRole("link", { name: /tasks/i }));

    expect(
      await screen.findByRole("heading", { name: "Tasks" }),
    ).toBeInTheDocument();
    expect(within(nav).getByRole("link", { name: /tasks/i })).toHaveAttribute(
      "href",
      `/app/projects/${project.id}/tasks`,
    );
    expect(within(nav).getByRole("link", { name: /tasks/i })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(
      within(nav).getByRole("link", { name: /organizations/i }),
    ).not.toHaveAttribute("aria-current");
    expect(
      within(nav).getByRole("link", { name: /projects/i }),
    ).not.toHaveAttribute("aria-current");
  });

  it("routes client accounts to the restricted ticket shell", async () => {
    mockFetch(jsonResponse(clientUser));

    renderRoute("/app");

    expect(
      await screen.findByRole("heading", { name: "My tickets" }),
    ).toBeInTheDocument();
    const nav = await screen.findByRole("navigation", {
      name: /primary navigation/i,
    });
    expect(
      within(nav).getByRole("link", { name: /my tickets/i }),
    ).toHaveAttribute("aria-current", "page");
    expect(
      within(nav).queryByRole("link", { name: /organizations/i }),
    ).not.toBeInTheDocument();
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
        name: "Selected work",
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

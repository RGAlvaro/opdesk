// Frontend organization route tests for SPEC-105.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppRouter } from "../../app/AppRouter";

const user = {
  id: "8847c8bf-2dd2-48f7-a3d1-5b1008700e4e",
  email: "user@example.com",
  full_name: "User Name",
  is_active: true,
  is_superuser: false,
  created_at: "2026-06-15T10:00:00Z",
  updated_at: "2026-06-15T10:00:00Z",
};

const ownerOrganization = {
  id: "9ed75133-2898-4d82-8d1c-0da379207144",
  name: "Acme Ops",
  slug: "acme-ops",
  role: "owner",
  created_at: "2026-06-20T10:00:00Z",
  updated_at: "2026-06-20T10:00:00Z",
};

const adminOrganization = {
  ...ownerOrganization,
  role: "admin",
};

const memberOrganization = {
  ...ownerOrganization,
  role: "member",
};

const memberUser = {
  id: "3ad4f913-c3e5-4f84-acdb-bd51c8d62eca",
  email: "member@example.com",
  full_name: "Member User",
  is_active: true,
};

const adminUser = {
  id: "88f4faba-02d4-4fbb-a29e-f92986338c27",
  email: "admin@example.com",
  full_name: "Admin User",
  is_active: true,
};

/** Build a JSON fetch response for mocked backend calls. */
function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/** Build an empty fetch response for endpoints like deletion. */
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

/** Build a paginated API response with default pagination metadata. */
function page<TItem>(items: TItem[]) {
  return {
    items,
    total: items.length,
    limit: 20,
    offset: 0,
  };
}

/** Build a membership response row for organization member tests. */
function membership(
  membershipUser: typeof memberUser,
  role: "owner" | "admin" | "member",
) {
  return {
    id: `${membershipUser.id}-membership`,
    user_id: membershipUser.id,
    organization_id: ownerOrganization.id,
    role,
    user: membershipUser,
    created_at: "2026-06-20T10:00:00Z",
    updated_at: "2026-06-20T10:00:00Z",
  };
}

/** Render the app router with isolated query and memory-router state. */
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

describe("SPEC-105 frontend organizations UI", () => {
  it("shows an empty organization list without fake data", async () => {
    mockFetch(jsonResponse(user), jsonResponse(page([])));

    renderRoute("/app/organizations");

    expect(
      await screen.findByRole("heading", { name: "Organizations" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Create your first workspace")).toBeInTheDocument();
    expect(screen.queryByText("Acme Ops")).not.toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: /new organization/i })[0],
    ).toHaveAttribute("href", "/app/organizations/new");
  });

  it("lists only backend-returned organizations with roles", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(
        page([
          ownerOrganization,
          {
            ...adminOrganization,
            id: "org-2",
            name: "Beta Ops",
            slug: "beta-ops",
          },
        ]),
      ),
    );

    renderRoute("/app/organizations");

    expect(await screen.findByText("Acme Ops")).toBeInTheDocument();
    expect(screen.getByText("Beta Ops")).toBeInTheDocument();
    expect(screen.getByText("Owner")).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("creates an organization and navigates to its detail page", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization, 201),
      jsonResponse(ownerOrganization),
    );
    const actor = userEvent.setup();

    renderRoute("/app/organizations/new");

    await actor.type(await screen.findByLabelText("Name"), "Acme Ops");
    await actor.type(screen.getByLabelText("Slug"), "acme-ops");
    await actor.click(
      screen.getByRole("button", { name: "Create organization" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Acme Ops" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/organizations",
      expect.objectContaining({
        credentials: "include",
        method: "POST",
      }),
    );
  });

  it("renders safe organization create errors", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("organization_slug_taken", "Organization slug is taken.", 409),
    );
    const actor = userEvent.setup();

    renderRoute("/app/organizations/new");

    await actor.type(await screen.findByLabelText("Name"), "Acme Ops");
    await actor.type(screen.getByLabelText("Slug"), "acme-ops");
    await actor.click(
      screen.getByRole("button", { name: "Create organization" }),
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Organization slug is taken.",
    );
  });

  it("shows member organization detail without owner or admin controls", async () => {
    mockFetch(jsonResponse(user), jsonResponse(memberOrganization));

    renderRoute(`/app/organizations/${ownerOrganization.id}`);

    expect(
      await screen.findByRole("heading", { name: "Acme Ops" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Member")).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Settings" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Members" }),
    ).not.toBeInTheDocument();
  });

  it("updates and deletes an owner organization from settings", async () => {
    const updatedOrganization = {
      ...ownerOrganization,
      name: "Updated Ops",
      slug: "updated-ops",
    };
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization),
      jsonResponse(updatedOrganization),
      jsonResponse(updatedOrganization),
      emptyResponse(),
      jsonResponse(page([])),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${ownerOrganization.id}/settings`);

    const name = await screen.findByLabelText("Name");
    await actor.clear(name);
    await actor.type(name, "Updated Ops");
    const slug = screen.getByLabelText("Slug");
    await actor.clear(slug);
    await actor.type(slug, "updated-ops");
    await actor.click(
      screen.getByRole("button", { name: "Save organization" }),
    );

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Organization updated.",
    );

    await actor.type(
      screen.getByLabelText(/type updated-ops to confirm/i),
      "updated-ops",
    );
    await actor.click(
      screen.getByRole("button", { name: "Delete organization" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Organizations" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/organizations/${ownerOrganization.id}`,
      expect.objectContaining({ credentials: "include", method: "DELETE" }),
    );
  });

  it("prevents non-owner settings edits in the UI", async () => {
    mockFetch(jsonResponse(user), jsonResponse(adminOrganization));

    renderRoute(`/app/organizations/${ownerOrganization.id}/settings`);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Only the organization owner can change settings.",
    );
    expect(
      screen.queryByRole("button", { name: "Save organization" }),
    ).not.toBeInTheDocument();
  });

  it("allows admins to view members without owner-only actions", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(adminOrganization),
      jsonResponse(
        page([membership(user, "owner"), membership(memberUser, "member")]),
      ),
    );

    renderRoute(`/app/organizations/${ownerOrganization.id}/members`);

    expect(
      await screen.findByRole("heading", { name: "Members" }),
    ).toBeInTheDocument();
    expect(await screen.findByText("member@example.com")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /remove/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /transfer ownership/i }),
    ).not.toBeInTheDocument();
  });

  it("lets owners manage non-owner members and transfer ownership", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization),
      jsonResponse(
        page([
          membership(user, "owner"),
          membership(memberUser, "member"),
          membership(adminUser, "admin"),
        ]),
      ),
      jsonResponse({ ...membership(memberUser, "admin"), role: "admin" }),
      jsonResponse(
        page([
          membership(user, "owner"),
          membership(memberUser, "admin"),
          membership(adminUser, "admin"),
        ]),
      ),
      emptyResponse(),
      jsonResponse(
        page([membership(user, "owner"), membership(memberUser, "admin")]),
      ),
      emptyResponse(),
      jsonResponse({ ...ownerOrganization, role: "admin" }),
      jsonResponse(
        page([membership(user, "admin"), membership(memberUser, "owner")]),
      ),
      jsonResponse(page([adminOrganization])),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${ownerOrganization.id}/members`);

    await screen.findByText("member@example.com");
    await actor.selectOptions(
      screen.getByLabelText("Role for member@example.com"),
      "admin",
    );

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/organizations/${ownerOrganization.id}/members/${memberUser.id}`,
        expect.objectContaining({ credentials: "include", method: "PATCH" }),
      ),
    );

    await actor.click(screen.getAllByRole("button", { name: "Remove" })[1]);
    await actor.click(screen.getByRole("button", { name: "Confirm remove" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/organizations/${ownerOrganization.id}/members/${adminUser.id}`,
        expect.objectContaining({ credentials: "include", method: "DELETE" }),
      ),
    );

    await actor.selectOptions(
      screen.getByLabelText("New owner"),
      memberUser.id,
    );
    await actor.click(
      screen.getByRole("button", { name: "Transfer ownership" }),
    );

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/organizations/${ownerOrganization.id}/transfer-ownership`,
        expect.objectContaining({ credentials: "include", method: "POST" }),
      ),
    );
  });

  it("renders safe not-found states and redirects unauthenticated routes", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("organization_not_found", "Organization not found.", 404),
    );

    renderRoute(`/app/organizations/${ownerOrganization.id}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Organization not found.",
    );

    vi.unstubAllGlobals();
    mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
    );

    renderRoute("/app/organizations");

    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });

  it("clears cached session and redirects when organization queries lose authentication", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("not_authenticated", "Authentication is required.", 401),
      apiError("not_authenticated", "Authentication is required.", 401),
    );

    renderRoute("/app/organizations");

    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });

  it("clears cached session and redirects when organization mutations lose authentication", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization),
      apiError("not_authenticated", "Authentication is required.", 401),
      apiError("not_authenticated", "Authentication is required.", 401),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${ownerOrganization.id}/settings`);

    const name = await screen.findByLabelText("Name");
    await actor.clear(name);
    await actor.type(name, "Updated Ops");
    await actor.click(
      screen.getByRole("button", { name: "Save organization" }),
    );

    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });
});

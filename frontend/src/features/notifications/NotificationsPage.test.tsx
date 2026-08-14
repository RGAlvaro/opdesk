// Frontend route tests for the SPEC-306 notification inbox.

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
  job_title: null,
  phone: null,
  timezone: null,
  locale: null,
  avatar_url: null,
  bio: null,
  is_active: true,
  is_superuser: false,
  created_at: "2026-06-15T10:00:00Z",
  updated_at: "2026-06-15T10:00:00Z",
};

const notification = {
  id: "2d2f96e3-ef1b-470f-b5a3-d9548a250f4b",
  recipient_user_id: user.id,
  type: "invitation.organization",
  title: "Organization invitation",
  body: "You were invited to Acme Ops.",
  action_url: "/app/invitations",
  resource_type: "invitation",
  resource_id: "511311d5-1608-49b4-9fd0-9f59deac09b0",
  read_at: null,
  created_at: "2026-08-14T10:00:00Z",
};

/** Build a JSON fetch response for mocked backend calls. */
function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
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

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SPEC-306 notification inbox UI", () => {
  it("shows unread state, marks notifications read, and opens invitation actions", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const method = init?.method ?? "GET";
      if (url.endsWith("/api/v1/users/me")) {
        return Promise.resolve(jsonResponse(user));
      }
      if (url.endsWith("/api/v1/notifications/unread-count")) {
        return Promise.resolve(jsonResponse({ unread_count: 1 }));
      }
      if (url.endsWith("/api/v1/notifications")) {
        return Promise.resolve(jsonResponse(page([notification])));
      }
      if (
        url.endsWith(`/api/v1/notifications/${notification.id}`) &&
        method === "PATCH"
      ) {
        return Promise.resolve(
          jsonResponse({
            ...notification,
            read_at: "2026-08-14T10:05:00Z",
          }),
        );
      }
      if (url.endsWith("/api/v1/invitations")) {
        return Promise.resolve(jsonResponse(page([])));
      }
      return Promise.resolve(
        jsonResponse({ error: { message: "Unexpected" } }, 500),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const actor = userEvent.setup();

    renderRoute("/app/notifications");

    expect(
      await screen.findByRole("heading", { name: "Notifications" }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Organization invitation"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("1 unread notifications")).toBeInTheDocument();

    await actor.click(screen.getByRole("button", { name: "Mark read" }));
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/notifications/${notification.id}`,
        expect.objectContaining({
          method: "PATCH",
          body: JSON.stringify({ read: true }),
        }),
      ),
    );

    await actor.click(screen.getByRole("link", { name: "Open" }));

    expect(
      await screen.findByRole("heading", { name: "My invitations" }),
    ).toBeInTheDocument();
  });
});

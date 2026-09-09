// Frontend route tests for the SPEC-306 notification inbox.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
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

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  listeners = new Map<string, Array<(event: MessageEvent | Event) => void>>();

  /** Track each notification socket and simulate a successful connection. */
  constructor(readonly url: string) {
    MockWebSocket.instances.push(this);
    queueMicrotask(() => this.emit("open", new Event("open")));
  }

  /** Register browser WebSocket listeners used by the notification hook. */
  addEventListener(
    type: string,
    listener: (event: MessageEvent | Event) => void,
  ) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  /** Notification sockets are receive-only in this spec. */
  send() {
    return undefined;
  }

  /** Close the socket and let tests emit close explicitly when needed. */
  close() {
    this.readyState = 3;
  }

  /** Emit one WebSocket event to registered listeners. */
  emit(type: string, event: MessageEvent | Event) {
    for (const listener of this.listeners.get(type) ?? []) {
      listener(event);
    }
  }
}

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
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.useRealTimers();
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

  it("updates the badge and inbox when a real-time notification arrives", async () => {
    let unreadCount = 0;
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/users/me")) {
        return Promise.resolve(jsonResponse(user));
      }
      if (url.endsWith("/api/v1/notifications/unread-count")) {
        return Promise.resolve(jsonResponse({ unread_count: unreadCount }));
      }
      if (url.endsWith("/api/v1/notifications")) {
        return Promise.resolve(jsonResponse(page([notification])));
      }
      return Promise.resolve(jsonResponse({ items: [] }));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/app/notifications");

    expect(
      await screen.findByRole("heading", { name: "Notifications" }),
    ).toBeInTheDocument();
    await waitFor(() => expect(MockWebSocket.instances).toHaveLength(1));
    expect(MockWebSocket.instances[0].listeners.get("message")).toHaveLength(1);

    unreadCount = 1;
    await act(async () => {
      MockWebSocket.instances[0].emit(
        "message",
        new MessageEvent("message", {
          data: JSON.stringify({
            type: "notification.created",
            notification,
            unread_count: 1,
          }),
        }),
      );
    });

    expect(await screen.findByText("Organization invitation")).toBeVisible();
    expect(await screen.findByText("1")).toBeVisible();
    expect(MockWebSocket.instances[0].url).toContain(
      "/api/v1/notifications/ws",
    );
  });

  it("invalidates REST state and reconnects after a socket close", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/api/v1/users/me")) {
        return Promise.resolve(jsonResponse(user));
      }
      if (url.endsWith("/api/v1/notifications/unread-count")) {
        return Promise.resolve(jsonResponse({ unread_count: 0 }));
      }
      if (url.endsWith("/api/v1/notifications")) {
        return Promise.resolve(jsonResponse(page([])));
      }
      return Promise.resolve(jsonResponse({ items: [] }));
    });
    vi.stubGlobal("fetch", fetchMock);

    renderRoute("/app/notifications");

    await waitFor(() => expect(MockWebSocket.instances).toHaveLength(1));
    vi.useFakeTimers();
    await act(async () => {
      MockWebSocket.instances[0].emit("close", new Event("close"));
      await vi.advanceTimersByTimeAsync(5_000);
    });

    expect(MockWebSocket.instances).toHaveLength(2);
    expect(
      fetchMock.mock.calls.filter(([url]) =>
        String(url).endsWith("/api/v1/notifications/unread-count"),
      ).length,
    ).toBeGreaterThanOrEqual(2);
  });
});

// Frontend coverage for SPEC-304 organization chat route behavior.

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ReactNode } from "react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AppRouter } from "../../app/AppRouter";

const currentUser = {
  id: "8847c8bf-2dd2-48f7-a3d1-5b1008700e4e",
  email: "owner@example.com",
  full_name: "Owner User",
  job_title: null,
  phone: null,
  timezone: null,
  locale: null,
  avatar_url: null,
  bio: null,
  is_active: true,
  is_superuser: false,
  account_type: "internal",
  created_at: "2026-08-18T10:00:00Z",
  updated_at: "2026-08-18T10:00:00Z",
};

const organizationId = "9ed75133-2898-4d82-8d1c-0da379207144";
const project = {
  id: "68163673-46be-4baa-97ec-9138258c6b7d",
  organization_id: organizationId,
  name: "Customer Onboarding",
  description: "Implementation work",
  is_archived: false,
  status: "active",
  start_date: null,
  end_date: null,
  budget_amount: null,
  budget_currency: null,
  visibility: "organization",
  project_owner_id: currentUser.id,
  created_at: "2026-08-18T10:00:00Z",
  updated_at: "2026-08-18T10:00:00Z",
};
const member = {
  user_id: "3ad4f913-c3e5-4f84-acdb-bd51c8d62eca",
  email: "member@example.com",
  full_name: "Member User",
  role: "member",
  shares_project: true,
};
const otherMember = {
  user_id: "60ef0b12-c829-4d61-a970-316fd54f087c",
  email: "other@example.com",
  full_name: "Other User",
  role: "member",
  shares_project: false,
};

type MockConversation = {
  id: string;
  organization_id: string;
  conversation_type: string;
  project_id: string | null;
  direct_user_id: string | null;
  unread_count: number;
  last_message: {
    id: string;
    conversation_id: string;
    organization_id: string;
    sender_id: string;
    body: string;
    created_at: string;
  } | null;
  created_at: string;
  updated_at: string;
};

const directConversation: MockConversation = {
  id: "b93464a0-daa8-43c1-81fc-0c0f7f7ecb6c",
  organization_id: organizationId,
  conversation_type: "direct",
  project_id: null,
  direct_user_id: member.user_id,
  unread_count: 0,
  last_message: null,
  created_at: "2026-08-18T10:00:00Z",
  updated_at: "2026-08-18T10:00:00Z",
};
const unreadConversation = {
  ...directConversation,
  unread_count: 2,
  last_message: {
    id: "ff41bd10-b168-43df-8f89-3ba89557eef9",
    conversation_id: directConversation.id,
    organization_id: organizationId,
    sender_id: member.user_id,
    body: "Unread update",
    created_at: "2026-08-18T10:05:00Z",
  },
};
const projectConversation = {
  ...directConversation,
  id: "47f8c452-199a-4604-a7b0-99d990117f66",
  conversation_type: "project_channel",
  project_id: project.id,
  direct_user_id: null,
};

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  readyState = MockWebSocket.OPEN;
  sent: string[] = [];
  listeners = new Map<string, Array<(event: MessageEvent | Event) => void>>();

  /** Track each created socket instance for assertions. */
  constructor(readonly url: string) {
    MockWebSocket.instances.push(this);
    queueMicrotask(() => this.emit("open", new Event("open")));
  }

  /** Register a test event listener for browser WebSocket callbacks. */
  addEventListener(
    type: string,
    listener: (event: MessageEvent | Event) => void,
  ) {
    this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
  }

  /** Record sent frames so tests can inspect socket traffic. */
  send(payload: string) {
    this.sent.push(payload);
  }

  /** Close the socket without simulating extra reconnect behavior. */
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

/** Mock backend fetch calls by URL and method for chat route tests. */
function mockChatFetch(conversation: MockConversation = directConversation) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (url === "/api/v1/users/me") {
      return Promise.resolve(jsonResponse(currentUser));
    }
    if (url.includes("/api/v1/notifications/unread-count")) {
      return Promise.resolve(jsonResponse({ unread_count: 0 }));
    }
    if (url.includes(`/api/v1/organizations/${organizationId}/chat/members`)) {
      return Promise.resolve(jsonResponse({ items: [member, otherMember] }));
    }
    if (url.includes(`/api/v1/organizations/${organizationId}/projects`)) {
      return Promise.resolve(
        jsonResponse({ items: [project], total: 1, limit: 100, offset: 0 }),
      );
    }
    if (
      method === "GET" &&
      url.includes(`/api/v1/organizations/${organizationId}/chat/conversations`)
    ) {
      return Promise.resolve(jsonResponse({ items: [conversation] }));
    }
    if (
      method === "POST" &&
      url.includes(
        `/api/v1/organizations/${organizationId}/chat/direct-conversations`,
      )
    ) {
      return Promise.resolve(jsonResponse(directConversation, 201));
    }
    if (
      method === "GET" &&
      url.includes(`/api/v1/projects/${project.id}/chat/channel`)
    ) {
      return Promise.resolve(jsonResponse(projectConversation));
    }
    if (
      method === "GET" &&
      url.includes(
        `/api/v1/chat/conversations/${directConversation.id}/messages`,
      )
    ) {
      return Promise.resolve(
        jsonResponse({
          items: [],
          total: 0,
          limit: 100,
          offset: 0,
        }),
      );
    }
    if (
      method === "POST" &&
      url.includes(`/api/v1/chat/conversations/${directConversation.id}/read`)
    ) {
      return Promise.resolve(jsonResponse(directConversation));
    }
    if (
      method === "POST" &&
      url.includes(`/api/v1/chat/conversations/${directConversation.id}/clear`)
    ) {
      return Promise.resolve(jsonResponse(directConversation));
    }
    return Promise.resolve(jsonResponse({ items: [] }));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

beforeEach(() => {
  vi.restoreAllMocks();
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SPEC-304 organization chat UI", () => {
  it("shows members, conversations, and a safe empty state", async () => {
    mockChatFetch();

    renderRoute(`/app/organizations/${organizationId}/chat`);

    expect(await screen.findByRole("heading", { name: "Chat" })).toBeVisible();
    expect(await screen.findByText("Member User")).toBeVisible();
    expect(screen.getByText("Shared project")).toBeVisible();
    expect(screen.getByText("Customer Onboarding")).toBeVisible();
    expect(screen.getByText("No conversation selected.")).toBeVisible();
  });

  it("opens a direct conversation and sends over WebSocket", async () => {
    const fetchMock = mockChatFetch();
    const user = userEvent.setup();

    renderRoute(`/app/organizations/${organizationId}/chat`);

    await user.click(
      await screen.findByRole("button", { name: /Member User/ }),
    );

    await waitFor(() => {
      expect(MockWebSocket.instances).toHaveLength(1);
    });
    await waitFor(() => {
      expect(MockWebSocket.instances[0].sent[0]).toContain("subscribe");
    });

    await user.type(
      screen.getByPlaceholderText("Write a message"),
      "Hello chat",
    );
    await user.click(screen.getByRole("button", { name: "Send" }));

    const sentFrames = MockWebSocket.instances[0].sent;
    expect(sentFrames[sentFrames.length - 1]).toContain("Hello chat");
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/organizations/${organizationId}/chat/direct-conversations`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("opens a project channel from the chat page", async () => {
    const fetchMock = mockChatFetch();
    const user = userEvent.setup();

    renderRoute(`/app/organizations/${organizationId}/chat`);

    await user.click(
      await screen.findByRole("button", { name: /Customer Onboarding/ }),
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/projects/${project.id}/chat/channel`,
        expect.objectContaining({ credentials: "include" }),
      );
    });
  });

  it("shows unread conversation state", async () => {
    mockChatFetch(unreadConversation);

    renderRoute(`/app/organizations/${organizationId}/chat`);

    expect(await screen.findByText("Unread update")).toBeVisible();
    expect(screen.getByText("2")).toBeVisible();
  });

  it("clears the selected conversation", async () => {
    const fetchMock = mockChatFetch();
    const user = userEvent.setup();

    renderRoute(
      `/app/organizations/${organizationId}/chat?conversation=${directConversation.id}`,
    );

    await user.click(await screen.findByRole("button", { name: "Clear" }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/chat/conversations/${directConversation.id}/clear`,
        expect.objectContaining({ method: "POST" }),
      );
    });
  });
});

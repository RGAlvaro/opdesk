// Frontend project and task route tests for SPEC-106.

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

const ownerOrganization = {
  id: "9ed75133-2898-4d82-8d1c-0da379207144",
  name: "Acme Ops",
  slug: "acme-ops",
  role: "owner",
  employee_count: 42,
  industry: "Logistics",
  website: "https://example.com",
  contact_email: "ops@example.com",
  phone: "+34 600 000 000",
  address_line1: "Main street 1",
  address_line2: null,
  city: "Madrid",
  region: "Madrid",
  postal_code: "28001",
  country: "Spain",
  tax_id: "ES12345678",
  logo_url: null,
  description: "Regional operations team",
  created_at: "2026-06-20T10:00:00Z",
  updated_at: "2026-06-20T10:00:00Z",
};

const memberOrganization = {
  ...ownerOrganization,
  role: "member",
};

const project = {
  id: "68163673-46be-4baa-97ec-9138258c6b7d",
  organization_id: ownerOrganization.id,
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

const archivedProject = {
  ...project,
  is_archived: true,
};

const memberUser = {
  id: "3ad4f913-c3e5-4f84-acdb-bd51c8d62eca",
  email: "member@example.com",
  full_name: "Member User",
  is_active: true,
};

const label = {
  id: "7e722880-69e0-478c-8521-5aa47949f1e8",
  organization_id: ownerOrganization.id,
  project_id: project.id,
  name: "Urgent customer",
  color: "#D92D20",
  description: "Customer-facing work",
  created_by_id: user.id,
  archived_at: null,
  created_at: "2026-06-21T11:00:00Z",
  updated_at: "2026-06-21T11:00:00Z",
};

const archivedLabel = {
  ...label,
  id: "84cc62dd-2af5-43af-81bb-68f9e3699b99",
  name: "Archived customer",
  archived_at: "2026-06-25T10:00:00Z",
};

const task = {
  id: "2c871fbd-4941-4505-8359-193d7a2d967c",
  organization_id: ownerOrganization.id,
  project_id: project.id,
  title: "Call customer",
  description: "Confirm kickoff agenda",
  status: "todo",
  priority: "high",
  assignee_id: memberUser.id,
  due_date: "2026-06-30",
  completed_at: null,
  estimated_hours: "2.00",
  actual_hours: null,
  sort_order: 10,
  blocked_reason: null,
  external_reference: "OPS-42",
  task_type: "operational",
  watcher_ids: [user.id],
  labels: [label],
  created_by_id: user.id,
  created_at: "2026-06-22T10:00:00Z",
  updated_at: "2026-06-22T10:00:00Z",
};

/** Build a JSON fetch response for mocked backend calls. */
function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
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

/** Build a paginated API response with configurable pagination metadata. */
function page<TItem>(
  items: TItem[],
  total = items.length,
  limit = 20,
  offset = 0,
) {
  return {
    items,
    total,
    limit,
    offset,
  };
}

/** Build a membership response row for assignment tests. */
function membership(membershipUser: typeof memberUser | typeof user) {
  return {
    id: `${membershipUser.id}-membership`,
    user_id: membershipUser.id,
    organization_id: ownerOrganization.id,
    role: membershipUser.id === user.id ? "owner" : "member",
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
  const queuedResponses = [...responses];
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";
    if (
      method === "GET" &&
      url.includes(`/api/v1/projects/${project.id}/labels`)
    ) {
      return Promise.resolve(jsonResponse(page([label])));
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

describe("SPEC-106 frontend projects and tasks UI", () => {
  it("lists organization projects with owner create controls", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization),
      jsonResponse(page([project], 40)),
      jsonResponse(
        page(
          [{ ...project, id: "second-project", name: "Second Project" }],
          40,
          20,
          20,
        ),
      ),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${ownerOrganization.id}/projects`);

    expect(
      await screen.findByRole("heading", { name: "Projects" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Customer Onboarding")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "New project" })).toHaveAttribute(
      "href",
      `/app/organizations/${ownerOrganization.id}/projects/new`,
    );
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/organizations/${ownerOrganization.id}/projects?limit=20&offset=0`,
      expect.objectContaining({ credentials: "include" }),
    );

    await actor.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("Second Project")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/organizations/${ownerOrganization.id}/projects?limit=20&offset=20`,
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("hides project creation controls for regular members", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(memberOrganization),
      jsonResponse(page([])),
    );

    renderRoute(`/app/organizations/${ownerOrganization.id}/projects`);

    expect(await screen.findByText("No projects yet")).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "New project" }),
    ).not.toBeInTheDocument();
  });

  it("creates a project and navigates to its detail route", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
      jsonResponse(project, 201),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/organizations/${ownerOrganization.id}/projects/new`);

    await actor.type(await screen.findByLabelText("Name"), project.name);
    await actor.type(
      screen.getByLabelText("Description"),
      "Implementation work",
    );
    await actor.click(screen.getByRole("button", { name: "Create project" }));

    expect(
      await screen.findByRole("heading", { name: project.name }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/organizations/${ownerOrganization.id}/projects`,
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
  });

  it("updates and archives a project from settings", async () => {
    const updatedProject = { ...project, name: "Updated Onboarding" };
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
      jsonResponse(updatedProject),
      jsonResponse({ ...updatedProject, is_archived: true }),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/projects/${project.id}/settings`);

    const name = await screen.findByLabelText("Name");
    await actor.clear(name);
    await actor.type(name, "Updated Onboarding");
    await actor.click(screen.getByRole("button", { name: "Save project" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Project updated.",
    );
    await actor.click(screen.getByRole("button", { name: "Archive project" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/projects/${project.id}`,
        expect.objectContaining({ credentials: "include", method: "PATCH" }),
      ),
    );
  });

  it("lets regular project members create labels from project detail", async () => {
    const createdLabel = {
      ...label,
      id: "24171ae5-3951-4d65-8c4a-4a7a126e7f3a",
      name: "Compliance",
      color: "#155EEF",
      description: "Audit follow-up",
    };
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(memberOrganization),
      jsonResponse(createdLabel, 201),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/projects/${project.id}`);

    expect(
      await screen.findByRole("heading", { name: project.name }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("link", { name: "Settings" }),
    ).not.toBeInTheDocument();
    await actor.type(await screen.findByLabelText("Label name"), "Compliance");
    await actor.clear(screen.getByLabelText("Label color"));
    await actor.type(screen.getByLabelText("Label color"), "#155EEF");
    await actor.type(
      screen.getByLabelText("Label description"),
      "Audit follow-up",
    );
    await actor.click(screen.getByRole("button", { name: "Add" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/projects/${project.id}/labels`,
        expect.objectContaining({
          credentials: "include",
          method: "POST",
          body: JSON.stringify({
            name: "Compliance",
            color: "#155EEF",
            description: "Audit follow-up",
          }),
        }),
      ),
    );
  });

  it("validates project label color before creation", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(memberOrganization),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/projects/${project.id}`);

    await actor.type(await screen.findByLabelText("Label name"), "Risk");
    await actor.clear(screen.getByLabelText("Label color"));
    await actor.type(screen.getByLabelText("Label color"), "red");
    await actor.click(screen.getByRole("button", { name: "Add" }));

    expect(
      await screen.findByText("Label color must use #RRGGBB."),
    ).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalledWith(
      `/api/v1/projects/${project.id}/labels`,
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("renders safe project not-found errors", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("project_not_found", "Project not found.", 404),
    );

    renderRoute(`/app/projects/${project.id}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Project not found.",
    );
  });

  it("lists tasks and keeps filters in backend query parameters", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(page([task], 40)),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
      jsonResponse(page([{ ...task, status: "done" }], 40)),
      jsonResponse(page([{ ...task, status: "done" }], 40)),
      jsonResponse(
        page(
          [{ ...task, id: "next-task", title: "Follow up", status: "done" }],
          40,
          20,
          20,
        ),
      ),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/projects/${project.id}/tasks`);

    expect(await screen.findByText("Call customer")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/projects/${project.id}/tasks?limit=20&offset=0`,
      expect.objectContaining({ credentials: "include" }),
    );
    await actor.selectOptions(screen.getByLabelText("Status"), "done");

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/projects/${project.id}/tasks?status=done&limit=20&offset=0`,
        expect.objectContaining({ credentials: "include" }),
      ),
    );
    await actor.selectOptions(screen.getByLabelText("Label"), label.id);

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/projects/${project.id}/tasks?status=done&label_id=${label.id}&limit=20&offset=0`,
        expect.objectContaining({ credentials: "include" }),
      ),
    );

    await actor.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText("Follow up")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/projects/${project.id}/tasks?status=done&label_id=${label.id}&limit=20&offset=20`,
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("loads project and task lists from shared pagination URLs", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(ownerOrganization),
      jsonResponse(page([project], 40, 20, 20)),
    );

    const firstRender = renderRoute(
      `/app/organizations/${ownerOrganization.id}/projects?limit=20&offset=20`,
    );

    expect(await screen.findByText("Customer Onboarding")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/organizations/${ownerOrganization.id}/projects?limit=20&offset=20`,
      expect.objectContaining({ credentials: "include" }),
    );

    firstRender.unmount();
    vi.unstubAllGlobals();
    const taskFetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(page([task], 40, 20, 20)),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
    );

    renderRoute(`/app/projects/${project.id}/tasks?limit=20&offset=20`);

    expect(await screen.findByText("Call customer")).toBeInTheDocument();
    expect(taskFetchMock).toHaveBeenCalledWith(
      `/api/v1/projects/${project.id}/tasks?limit=20&offset=20`,
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("creates an owner-assigned task and navigates to detail", async () => {
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
      jsonResponse(task, 201),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/projects/${project.id}/tasks/new`);

    await actor.type(await screen.findByLabelText("Title"), "Call customer");
    await actor.selectOptions(screen.getByLabelText("Priority"), "high");
    await actor.selectOptions(screen.getByLabelText("Assignee"), memberUser.id);
    await actor.click(screen.getByRole("button", { name: "Create task" }));

    expect(
      await screen.findByRole("heading", { name: "Call customer" }),
    ).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      `/api/v1/projects/${project.id}/tasks`,
      expect.objectContaining({ credentials: "include", method: "POST" }),
    );
  });

  it("limits regular member task creation assignment choices to unassigned or self", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse(project),
      jsonResponse(memberOrganization),
    );

    renderRoute(`/app/projects/${project.id}/tasks/new`);

    const assignee = await screen.findByLabelText("Assignee");
    expect(assignee).toHaveTextContent("Unassigned");
    expect(assignee).toHaveTextContent("Me");
    expect(assignee).not.toHaveTextContent("Member User");
  });

  it("prevents task creation for archived projects", async () => {
    mockFetch(jsonResponse(user), jsonResponse(archivedProject));

    renderRoute(`/app/projects/${project.id}/tasks/new`);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Archived projects do not accept new tasks.",
    );
  });

  it("updates assigned task status from backend-returned completion state", async () => {
    const doneTask = {
      ...task,
      assignee_id: user.id,
      status: "done",
      completed_at: "2026-06-24T10:00:00Z",
    };
    mockFetch(
      jsonResponse(user),
      jsonResponse({ ...task, assignee_id: user.id }),
      jsonResponse(project),
      jsonResponse(memberOrganization),
      jsonResponse(doneTask),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/tasks/${task.id}`);

    await actor.selectOptions(await screen.findByLabelText("Status"), "done");
    await actor.click(screen.getByRole("button", { name: "Save task" }));

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Task updated.",
    );
    await waitFor(() =>
      expect(screen.getAllByText("Completed").length).toBeGreaterThan(0),
    );
  });

  it("applies active labels from editable task detail", async () => {
    const unlabeledTask = { ...task, labels: [] };
    const labeledTask = { ...task, labels: [label] };
    const fetchMock = mockFetch(
      jsonResponse(user),
      jsonResponse(unlabeledTask),
      jsonResponse(project),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
      jsonResponse(labeledTask),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/tasks/${task.id}`);

    await actor.click(await screen.findByRole("button", { name: label.name }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/v1/tasks/${task.id}/labels`,
        expect.objectContaining({
          credentials: "include",
          method: "POST",
          body: JSON.stringify({ label_id: label.id }),
        }),
      ),
    );
  });

  it("renders archived task labels without offering them for assignment", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse({ ...task, labels: [archivedLabel] }),
      jsonResponse(project),
      jsonResponse(ownerOrganization),
      jsonResponse(page([membership(user), membership(memberUser)])),
    );

    renderRoute(`/app/tasks/${task.id}`);

    expect(await screen.findByText(archivedLabel.name)).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: archivedLabel.name }),
    ).not.toBeInTheDocument();
  });

  it("renders safe task update permission errors", async () => {
    mockFetch(
      jsonResponse(user),
      jsonResponse({ ...task, assignee_id: user.id }),
      jsonResponse(project),
      jsonResponse(memberOrganization),
      apiError("insufficient_role", "Insufficient role.", 403),
    );
    const actor = userEvent.setup();

    renderRoute(`/app/tasks/${task.id}`);

    await actor.selectOptions(await screen.findByLabelText("Status"), "done");
    await actor.click(screen.getByRole("button", { name: "Save task" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Insufficient role.",
    );
  });

  it("renders safe task not-found errors", async () => {
    mockFetch(
      jsonResponse(user),
      apiError("task_not_found", "Task not found.", 404),
    );

    renderRoute(`/app/tasks/${task.id}`);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Task not found.",
    );
  });

  it("redirects project and task routes when unauthenticated", async () => {
    mockFetch(
      apiError("not_authenticated", "Authentication is required.", 401),
    );

    renderRoute(`/app/projects/${project.id}/tasks`);

    expect(
      await screen.findByRole("heading", { name: "Log in" }),
    ).toBeInTheDocument();
  });
});

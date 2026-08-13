// Shared Playwright helpers for authenticated OpsDesk browser workflows.

import { expect, type APIRequestContext, type Page } from "@playwright/test";

export const e2ePassword = "Example1234";

export type E2EUser = {
  email: string;
  fullName: string;
  password: string;
};

export type E2EOrganization = {
  id: string;
  name: string;
};

export type E2EProject = {
  id: string;
  organization_id: string;
  name: string;
};

export type E2ETask = {
  id: string;
  project_id: string;
  title: string;
};

export type E2ELabel = {
  id: string;
  name: string;
};

/** Build a unique suffix so repeated local and CI runs do not collide. */
export function runSuffix() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

/** Create deterministic E2E user credentials for one test run. */
export function e2eUser(suffix: string, fullName = "E2E Owner"): E2EUser {
  return {
    email: `e2e-${suffix}@example.com`,
    fullName,
    password: e2ePassword,
  };
}

/** Return the authenticated primary navigation landmark. */
export function primaryNavigation(page: Page) {
  return page.getByRole("navigation", { name: "Primary navigation" });
}

/** Assert that the authenticated app shell is showing the expected user. */
export async function expectAppShell(page: Page, user: E2EUser) {
  await expect(
    page.getByRole("heading", { name: /workspace overview/i }),
  ).toBeVisible();
  await expect(page.getByText(user.email)).toBeVisible();
}

/** Send a public API request and return parsed JSON with useful failure context. */
async function apiJson<TResponse>(
  request: APIRequestContext,
  method: "post" | "patch",
  path: string,
  data: unknown,
) {
  const response = await request[method](path, { data });
  if (!response.ok()) {
    throw new Error(
      `${method.toUpperCase()} ${path} failed with ${response.status()}: ${await response.text()}`,
    );
  }
  return (await response.json()) as TResponse;
}

/** Register a user through the public auth API without creating a browser session. */
export async function createUserViaApi(page: Page, user: E2EUser) {
  await apiJson(page.request, "post", "/api/v1/auth/register", {
    email: user.email,
    password: user.password,
    full_name: user.fullName,
  });
}

/** Log in through the public auth API so the browser context receives auth cookies. */
export async function loginViaApi(page: Page, user: E2EUser) {
  await apiJson(page.request, "post", "/api/v1/auth/login", {
    email: user.email,
    password: user.password,
  });
}

/** Fill the visible login form and wait until the authenticated shell is visible. */
export async function loginViaUi(page: Page, user: E2EUser) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: "Log in" }).click();
  await expectAppShell(page, user);
}

/** Fill the signup form and wait until the authenticated shell is visible. */
export async function signUpViaUi(page: Page, user: E2EUser) {
  await page.goto("/signup");
  await page.getByLabel("Full name").fill(user.fullName);
  await page.getByLabel("Email").fill(user.email);
  await page.getByLabel("Password").fill(user.password);
  await page.getByRole("button", { name: "Create account" }).click();
  await expectAppShell(page, user);
}

/** Create and authenticate a user through public APIs for setup-heavy tests. */
export async function createAuthenticatedUser(page: Page, suffix: string) {
  const user = e2eUser(suffix);
  await createUserViaApi(page, user);
  await loginViaApi(page, user);
  return user;
}

/** Create an organization through the public API for the authenticated user. */
export async function createOrganizationViaApi(
  page: Page,
  name: string,
): Promise<E2EOrganization> {
  return apiJson<E2EOrganization>(
    page.request,
    "post",
    "/api/v1/organizations",
    {
      name,
      description: "Created by Playwright E2E setup.",
    },
  );
}

/** Create a project through the public API for an existing organization. */
export async function createProjectViaApi(
  page: Page,
  organizationId: string,
  name: string,
): Promise<E2EProject> {
  return apiJson<E2EProject>(
    page.request,
    "post",
    `/api/v1/organizations/${organizationId}/projects`,
    {
      name,
      description: "Created by Playwright E2E setup.",
      status: "active",
      visibility: "organization",
    },
  );
}

/** Create a task through the public API for an existing project. */
export async function createTaskViaApi(
  page: Page,
  projectId: string,
  payload: {
    title: string;
    priority?: string;
    due_date?: string;
    external_reference?: string;
  },
): Promise<E2ETask> {
  return apiJson<E2ETask>(
    page.request,
    "post",
    `/api/v1/projects/${projectId}/tasks`,
    {
      title: payload.title,
      description: "Created by Playwright E2E setup.",
      priority: payload.priority ?? "medium",
      due_date: payload.due_date ?? null,
      external_reference: payload.external_reference ?? null,
      task_type: "internal",
    },
  );
}

/** Update task fields through the public API when setup needs specific state. */
export async function updateTaskViaApi(
  page: Page,
  taskId: string,
  payload: Record<string, unknown>,
): Promise<E2ETask> {
  return apiJson<E2ETask>(
    page.request,
    "patch",
    `/api/v1/tasks/${taskId}`,
    payload,
  );
}

/** Create one project label through the public labels API. */
export async function createLabelViaApi(
  page: Page,
  projectId: string,
  name: string,
): Promise<E2ELabel> {
  return apiJson<E2ELabel>(
    page.request,
    "post",
    `/api/v1/projects/${projectId}/labels`,
    {
      name,
      color: "#2563EB",
      description: "Created by Playwright E2E setup.",
    },
  );
}

/** Assign one existing project label to one task through the public labels API. */
export async function assignLabelViaApi(
  page: Page,
  taskId: string,
  labelId: string,
) {
  await apiJson(page.request, "post", `/api/v1/tasks/${taskId}/labels`, {
    label_id: labelId,
  });
}

/** Build a minimal organization and project for an authenticated user. */
export async function createWorkspaceViaApi(page: Page, suffix: string) {
  const organization = await createOrganizationViaApi(
    page,
    `E2E Organization ${suffix}`,
  );
  const project = await createProjectViaApi(
    page,
    organization.id,
    `E2E Project ${suffix}`,
  );
  return { organization, project };
}

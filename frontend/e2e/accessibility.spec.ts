// Automated accessibility checks for public and authenticated OpsDesk pages.

import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import {
  createAuthenticatedUser,
  createProjectClientViaApi,
  createTaskViaApi,
  createWorkspaceViaApi,
  e2eUser,
  loginViaApi,
  runSuffix,
} from "./helpers";

type AxeNode = {
  target: string[];
};

type AxeViolation = {
  id: string;
  impact: string | null;
  help: string;
  nodes: AxeNode[];
};

/** Fail with route-specific context for serious automated accessibility issues. */
async function expectNoSeriousAccessibilityViolations(
  page: Page,
  routeName: string,
) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  const seriousViolations = results.violations.filter((violation) =>
    ["serious", "critical"].includes(violation.impact ?? ""),
  ) as AxeViolation[];

  const failureSummary = seriousViolations
    .map((violation) => {
      const targets = violation.nodes
        .flatMap((node) => node.target)
        .slice(0, 5)
        .join(", ");
      return `${routeName}: ${violation.id} (${violation.impact}) ${violation.help} [${targets}]`;
    })
    .join("\n");

  expect(seriousViolations, failureSummary).toEqual([]);
}

test.describe("SPEC-313 accessibility coverage", () => {
  test("public routes have no serious automated accessibility violations", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Accessibility coverage runs once on desktop Chromium.",
    );

    await page.goto("/");
    await expect(
      page.getByRole("heading", {
        name: /production-minded SaaS projects/i,
      }),
    ).toBeVisible();
    await expectNoSeriousAccessibilityViolations(page, "public home");

    await page.goto("/changelog");
    await expect(
      page.getByRole("heading", { name: "Changelog" }),
    ).toBeVisible();
    await expectNoSeriousAccessibilityViolations(page, "public changelog");

    await page.goto("/login");
    await expect(page.getByRole("heading", { name: "Log in" })).toBeVisible();
    await expectNoSeriousAccessibilityViolations(page, "login");
  });

  test("authenticated app pages have no serious automated accessibility violations", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Accessibility coverage runs once on desktop Chromium.",
    );

    const suffix = runSuffix();
    await createAuthenticatedUser(page, suffix);
    const { project } = await createWorkspaceViaApi(page, suffix);
    const task = await createTaskViaApi(page, project.id, {
      title: `E2E A11y Task ${suffix}`,
    });

    await page.goto("/app");
    await expect(
      page.getByRole("heading", { name: /workspace overview/i }),
    ).toBeVisible();
    await expectNoSeriousAccessibilityViolations(page, "app shell");

    await page.goto("/app/notifications");
    await expect(
      page.getByRole("heading", { name: "Notifications" }),
    ).toBeVisible();
    await expectNoSeriousAccessibilityViolations(page, "notifications inbox");

    await page.goto(`/app/projects/${project.id}/tasks`);
    await expect(page.getByRole("link", { name: task.title })).toBeVisible();
    await expectNoSeriousAccessibilityViolations(page, "project task list");
  });

  test("client ticket shell has no serious automated accessibility violations", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Client accessibility coverage runs once on desktop Chromium.",
    );

    const suffix = runSuffix();
    await createAuthenticatedUser(page, suffix);
    const { project } = await createWorkspaceViaApi(page, suffix);
    const clientUser = e2eUser(`client-${suffix}`, "E2E Client");
    await createProjectClientViaApi(page, project.id, clientUser);

    await loginViaApi(page, clientUser);
    await page.goto("/app/client");
    await expect(
      page.getByRole("heading", { name: "My tickets" }),
    ).toBeVisible();
    await expect(page.getByLabel("Project")).toContainText(project.name);
    await expectNoSeriousAccessibilityViolations(page, "client ticket list");
  });
});

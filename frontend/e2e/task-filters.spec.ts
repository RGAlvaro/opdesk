// Browser E2E coverage for task filters, URL state, and label filtering.

import { expect, test } from "@playwright/test";

import {
  assignLabelViaApi,
  createAuthenticatedUser,
  createLabelViaApi,
  createTaskViaApi,
  createWorkspaceViaApi,
  runSuffix,
  updateTaskViaApi,
} from "./helpers";

test.describe("SPEC-312 task filter browser coverage", () => {
  test("persists task filters and label filters in the URL", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Filter coverage runs once on desktop Chromium.",
    );

    const suffix = runSuffix();
    await createAuthenticatedUser(page, suffix);
    const { project } = await createWorkspaceViaApi(page, suffix);
    const label = await createLabelViaApi(
      page,
      project.id,
      `E2E Label ${suffix}`,
    );
    const matchingTaskTitle = `E2E Matching Task ${suffix}`;
    const hiddenTodoTitle = `E2E Hidden Todo ${suffix}`;
    const hiddenPriorityTitle = `E2E Hidden Priority ${suffix}`;
    const hiddenLabelTitle = `E2E Hidden Label ${suffix}`;

    const matchingTask = await createTaskViaApi(page, project.id, {
      title: matchingTaskTitle,
      priority: "high",
      due_date: "2026-09-15",
    });
    await updateTaskViaApi(page, matchingTask.id, { status: "done" });
    await assignLabelViaApi(page, matchingTask.id, label.id);

    const hiddenTodo = await createTaskViaApi(page, project.id, {
      title: hiddenTodoTitle,
      priority: "high",
      due_date: "2026-09-15",
    });
    await assignLabelViaApi(page, hiddenTodo.id, label.id);

    const hiddenPriority = await createTaskViaApi(page, project.id, {
      title: hiddenPriorityTitle,
      priority: "low",
      due_date: "2026-09-15",
    });
    await updateTaskViaApi(page, hiddenPriority.id, { status: "done" });
    await assignLabelViaApi(page, hiddenPriority.id, label.id);

    const hiddenLabel = await createTaskViaApi(page, project.id, {
      title: hiddenLabelTitle,
      priority: "high",
      due_date: "2026-09-15",
    });
    await updateTaskViaApi(page, hiddenLabel.id, { status: "done" });

    await page.goto(`/app/projects/${project.id}/tasks`);
    await expect(
      page.getByRole("link", { name: matchingTaskTitle }),
    ).toBeVisible();

    await page.getByLabel("Status").selectOption("done");
    await page.getByLabel("Priority").selectOption("high");
    await page.getByLabel("Due after").fill("2026-09-01");
    await page.getByLabel("Due before").fill("2026-09-30");
    await expect(page.getByLabel("Label")).toContainText(label.name);
    await page.getByLabel("Label").selectOption({ label: label.name });

    await expect(page).toHaveURL(/status=done/);
    await expect(page).toHaveURL(/priority=high/);
    await expect(page).toHaveURL(/due_after=2026-09-01/);
    await expect(page).toHaveURL(/due_before=2026-09-30/);
    await expect(page).toHaveURL(new RegExp(`label_id=${label.id}`));
    await expect(
      page.getByRole("link", { name: matchingTaskTitle }),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: hiddenTodoTitle }),
    ).not.toBeVisible();
    await expect(
      page.getByRole("link", { name: hiddenPriorityTitle }),
    ).not.toBeVisible();
    await expect(
      page.getByRole("link", { name: hiddenLabelTitle }),
    ).not.toBeVisible();

    await page.reload();
    await expect(page.getByLabel("Status")).toHaveValue("done");
    await expect(page.getByLabel("Priority")).toHaveValue("high");
    await expect(page.getByLabel("Due after")).toHaveValue("2026-09-01");
    await expect(page.getByLabel("Due before")).toHaveValue("2026-09-30");
    await expect(page.getByLabel("Label")).toHaveValue(label.id);
    await expect(
      page.getByRole("link", { name: matchingTaskTitle }),
    ).toBeVisible();
  });
});

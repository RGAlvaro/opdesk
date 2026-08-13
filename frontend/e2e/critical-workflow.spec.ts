// Critical browser workflow coverage for auth, organizations, projects, and tasks.

import { expect, test } from "@playwright/test";

import { e2eUser, primaryNavigation, runSuffix, signUpViaUi } from "./helpers";

test("signup to completed task critical path", async ({ page }) => {
  const suffix = runSuffix();
  const user = e2eUser(suffix);
  const organizationName = `E2E Organization ${suffix}`;
  const projectName = `E2E Project ${suffix}`;
  const taskTitle = `E2E Task ${suffix}`;
  const navigation = primaryNavigation(page);

  await signUpViaUi(page, user);

  await navigation
    .getByRole("link", { name: "Organizations", exact: true })
    .click();
  await page.getByRole("link", { name: "New organization" }).first().click();
  await page.getByLabel("Name").fill(organizationName);
  await page
    .getByLabel("Description")
    .fill("Created by the Playwright critical path test.");
  await page.getByRole("button", { name: "Create organization" }).click();

  await expect(
    page.getByRole("heading", { name: organizationName }),
  ).toBeVisible();
  await navigation.getByRole("link", { name: "Projects", exact: true }).click();

  await page.getByRole("link", { name: "New project" }).first().click();
  await page.getByLabel("Name").fill(projectName);
  await page
    .getByLabel("Description")
    .fill("Project created during the critical E2E workflow.");
  await page.getByRole("button", { name: "Create project" }).click();

  await expect(page.getByRole("heading", { name: projectName })).toBeVisible();
  await navigation.getByRole("link", { name: "Tasks", exact: true }).click();
  await page.getByRole("link", { name: "New task" }).click();

  await page.getByLabel("Title").fill(taskTitle);
  await page
    .getByLabel("Description")
    .fill("Task created and completed through the real browser workflow.");
  await page.getByRole("button", { name: "Create task" }).click();

  await expect(page.getByRole("heading", { name: taskTitle })).toBeVisible();
  await page.getByLabel("Status").selectOption("done");
  await page.getByRole("button", { name: "Save task" }).click();

  await expect(page.getByRole("status")).toContainText("Task updated.");
  await expect(page.getByText("Completed").first()).toBeVisible();
  await expect(page.getByText("Done").first()).toBeVisible();
});

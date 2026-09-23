// Browser E2E coverage for auth protection, login, logout, and profile updates.

import { expect, test } from "@playwright/test";

import {
  createAuthenticatedUser,
  createUserViaApi,
  e2eUser,
  expectAppShell,
  loginViaUi,
  runSuffix,
} from "./helpers";

test.describe("SPEC-312 auth and profile browser coverage", () => {
  test("redirects protected routes to login without a session", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Protected-route coverage runs once on desktop Chromium.",
    );

    for (const path of [
      "/app",
      "/app/profile",
      "/app/projects/00000000-0000-0000-0000-000000000000/tasks",
    ]) {
      await page.goto(path);
      await expect(page).toHaveURL(/\/login$/);
      await expect(
        page.getByRole("heading", { name: /workspace overview/i }),
      ).not.toBeVisible();
    }
  });

  test("logs in, logs out, and protects routes after logout", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Login/logout coverage runs once on desktop Chromium.",
    );

    const user = e2eUser(runSuffix());
    await createUserViaApi(page, user);

    await loginViaUi(page, user);
    await expect(page).toHaveURL(/\/app$/);

    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(
      page.getByRole("heading", { name: "Selected work" }),
    ).toBeVisible();

    await page.goto("/app/profile");
    await expect(page).toHaveURL(/\/login$/);
  });

  test("persists profile updates across navigation and refresh", async ({
    page,
  }, testInfo) => {
    test.skip(
      testInfo.project.name !== "chromium-desktop",
      "Profile coverage runs once on desktop Chromium.",
    );

    const suffix = runSuffix();
    const user = await createAuthenticatedUser(page, suffix);
    const updatedName = `E2E Renamed ${suffix}`;

    await page.goto("/app/profile");
    await page.getByLabel("Full name").fill(updatedName);
    await page.getByLabel("Job title").fill("E2E Coordinator");
    await page.getByLabel("Bio").fill("Profile update checked by Playwright.");
    await page.getByRole("button", { name: "Save changes" }).click();

    await expect(page.getByRole("status")).toContainText("Profile updated.");
    await expect(page.getByText(updatedName)).toBeVisible();

    await page.goto("/app");
    await expectAppShell(page, { ...user, fullName: updatedName });

    await page.goto("/app/profile");
    await page.reload();
    await expect(page.getByLabel("Full name")).toHaveValue(updatedName);
    await expect(page.getByLabel("Job title")).toHaveValue("E2E Coordinator");
  });
});

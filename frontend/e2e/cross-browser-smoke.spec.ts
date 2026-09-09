// Focused Firefox/WebKit smoke coverage for public routes and core authenticated flows.

import { expect, test } from "@playwright/test";

import {
  createProjectViaApi,
  e2eUser,
  loginViaUi,
  primaryNavigation,
  runSuffix,
  signUpViaUi,
} from "./helpers";

test.describe("SPEC-313 Firefox and WebKit smoke coverage", () => {
  test("loads public routes, protects app routes, and completes auth smoke", async ({
    page,
  }, testInfo) => {
    test.skip(
      !["firefox-smoke", "webkit-smoke"].includes(testInfo.project.name),
      "Cross-browser smoke runs only on Firefox and WebKit projects.",
    );

    const suffix = runSuffix();
    const user = e2eUser(suffix, `E2E Browser ${suffix}`);
    const organizationName = `E2E Browser Org ${suffix}`;
    const projectName = `E2E Browser Project ${suffix}`;

    await page.goto("/");
    await expect(
      page.getByRole("heading", {
        name: /production-minded SaaS projects/i,
      }),
    ).toBeVisible();

    await page.goto("/changelog");
    await expect(
      page.getByRole("heading", { name: "Changelog" }),
    ).toBeVisible();

    await page.goto("/app");
    await expect(page).toHaveURL(/\/login$/);

    await signUpViaUi(page, user);
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(
      page.getByRole("heading", {
        name: /production-minded SaaS projects/i,
      }),
    ).toBeVisible();

    await loginViaUi(page, user);
    await primaryNavigation(page)
      .getByRole("link", { name: "Organizations", exact: true })
      .click();
    await page.getByRole("link", { name: "New organization" }).first().click();
    await page.getByLabel("Name").fill(organizationName);
    await page
      .getByLabel("Description")
      .fill("Created by Firefox/WebKit smoke coverage.");
    await page.getByRole("button", { name: "Create organization" }).click();
    await expect(
      page.getByRole("heading", { name: organizationName }),
    ).toBeVisible();

    const createdOrganization = page
      .url()
      .match(/\/app\/organizations\/([^/?#]+)/);
    expect(createdOrganization?.[1]).toBeTruthy();
    await createProjectViaApi(page, createdOrganization![1], projectName);

    await primaryNavigation(page)
      .getByRole("link", { name: "Projects", exact: true })
      .click();
    await expect(page.getByRole("link", { name: projectName })).toBeVisible();

    await page.getByRole("button", { name: "Sign out" }).click();
    await page.goto("/app/profile");
    await expect(page).toHaveURL(/\/login$/);
  });
});

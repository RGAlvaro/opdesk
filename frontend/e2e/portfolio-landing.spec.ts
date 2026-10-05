// Browser checks and review captures for the SPEC-318/319 public landing layout.

import { expect, test } from "@playwright/test";

test.describe("SPEC-318/319 portfolio landing", () => {
  for (const width of [390, 768, 1440]) {
    test(`keeps the portfolio usable at ${width}px`, async ({
      page,
    }, testInfo) => {
      test.skip(
        testInfo.project.name !== "chromium-desktop",
        "The three layout widths run once in Chromium.",
      );

      await page.setViewportSize({ width, height: 900 });
      await page.goto("/");
      await expect(
        page.getByRole("heading", { name: "Selected work" }),
      ).toBeVisible();
      await expect(page.getByText(/ideas · tools · better days/i)).toHaveCount(
        0,
      );

      const opsDesk = page.getByRole("region", { name: "OpsDesk" });
      const approach = page.getByRole("region", { name: "My approach" });
      const eventflow = page.getByRole("region", { name: "EventFlow" });
      await expect(opsDesk.getByText("Available")).toBeVisible();
      await expect(
        opsDesk.getByRole("link", { name: "Open OpsDesk" }),
      ).toHaveAttribute("href", "/login");
      await expect(
        opsDesk.getByRole("link", { name: "Create account" }),
      ).toHaveAttribute("href", "/signup");
      await expect(approach.getByRole("listitem")).toHaveCount(4);
      await expect(eventflow.getByText("Code available")).toBeVisible();
      await expect(
        eventflow.getByText(
          /durable event ingestion and signed webhook delivery/i,
        ),
      ).toBeVisible();
      await expect(
        eventflow.getByText(
          /interface and live demo are still in development/i,
        ),
      ).toBeVisible();
      await expect(eventflow.locator("img.portfolio-next__art")).toBeVisible();
      await expect(
        eventflow.getByRole("link", { name: "View repository" }),
      ).toHaveAttribute("href", "https://github.com/RGAlvaro/eventflow");
      await expect(eventflow.getByRole("link")).toHaveCount(1);
      await expect(
        page.getByRole("navigation", { name: "Footer navigation" }),
      ).toBeVisible();

      const hasHorizontalOverflow = await page.evaluate(
        () => document.documentElement.scrollWidth > window.innerWidth,
      );
      expect(hasHorizontalOverflow).toBe(false);

      if (width !== 768) {
        await page.screenshot({
          path: testInfo.outputPath(`portfolio-landing-${width}.png`),
          fullPage: true,
        });
      }
    });
  }
});

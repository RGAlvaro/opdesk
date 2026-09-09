// Playwright configuration for full-stack browser checks against local OpsDesk services.

import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:5173";

/** Configure browser E2E tests to reuse the Docker/Vite frontend URL by default. */
export default defineConfig({
  testDir: "./e2e",
  outputDir: process.env.PLAYWRIGHT_OUTPUT_DIR ?? "test-results",
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : "list",
  use: {
    baseURL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium-desktop",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "chromium-mobile",
      use: { ...devices["Pixel 7"] },
      testMatch: /critical-workflow\.spec\.ts/,
    },
    {
      name: "firefox-smoke",
      use: { ...devices["Desktop Firefox"] },
      testMatch: /cross-browser-smoke\.spec\.ts/,
    },
    {
      name: "webkit-smoke",
      use: { ...devices["Desktop Safari"] },
      testMatch: /cross-browser-smoke\.spec\.ts/,
    },
  ],
});

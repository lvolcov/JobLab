// joblab — Playwright config
// Purpose: run e2e + screenshot tests against the running compose stack.
//
// Assumes:
//   - api is reachable at http://localhost:8010 with JOBLAB_TEST_MODE=1
//   - web is reachable at http://localhost:5173
//   - the seeded admin account (admin@example.com) exists
//
// Tests do NOT require a clean DB — each test creates its own isolated user
// via the admin API (see tests/e2e/helpers.ts::createTestUser).

import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:5173";

export default defineConfig({
  testDir: "./tests/e2e",
  snapshotDir: "./tests/screenshots",
  fullyParallel: false, // shared DB state — serialise.
  workers: 1,
  retries: 0,
  reporter: [["list"]],
  timeout: 60_000,
  expect: {
    timeout: 10_000,
    toHaveScreenshot: {
      // Real-world rendering varies slightly across machines; allow a small
      // diff so committed baselines remain useful across hosts.
      maxDiffPixelRatio: 0.02,
      animations: "disabled",
      caret: "hide",
    },
  },
  use: {
    baseURL: BASE_URL,
    headless: true,
    viewport: { width: 1280, height: 800 },
    locale: "en-GB",
    timezoneId: "Europe/London",
    actionTimeout: 10_000,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});

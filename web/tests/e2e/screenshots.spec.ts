// Screenshot baselines for every top-level route, light + dark.
//
// First-time run:   `pnpm test:e2e:update` to capture baselines on your host.
// Subsequent runs:  `pnpm test:e2e` validates diffs are within tolerance.
//
// Isolation:
//  - Non-admin routes are captured under a fresh test user with no data, so
//    the screenshots are deterministic regardless of what's in the DB.
//  - Admin routes are captured under the seeded admin, but data-bearing
//    regions (tables, lists) are masked because their row counts depend on
//    what other tests have done.
//
// Tolerance is set in playwright.config.ts (maxDiffPixelRatio: 0.02) because
// font rendering varies subtly between machines and OSes.

import { expect, test } from "@playwright/test";
import { createTestUser, login, setTheme } from "./helpers";

const USER_ROUTES = [
  { name: "dashboard", path: "/" },
  { name: "wiki-cvs", path: "/wiki/cvs" },
  { name: "wiki-experiences", path: "/wiki/experiences" },
  { name: "applications", path: "/applications" },
  { name: "settings", path: "/settings" },
];

const ADMIN_ROUTES = [
  { name: "admin-users", path: "/admin/users", maskSelector: "table tbody" },
  { name: "admin-llm-keys", path: "/admin/llm-keys", maskSelector: "ul, table tbody" },
];

for (const theme of ["light", "dark"] as const) {
  test.describe(`screenshots — ${theme}`, () => {
    test("login page", async ({ page }) => {
      await setTheme(page, theme);
      await page.goto("/login");
      await expect(page.getByText("Sign in")).toBeVisible();
      await expect(page).toHaveScreenshot(`login-${theme}.png`, { fullPage: true });
    });

    for (const { name, path } of USER_ROUTES) {
      test(name, async ({ page }) => {
        await setTheme(page, theme);
        await createTestUser(page);
        await page.goto(path);
        await page.waitForLoadState("networkidle");
        await expect(page).toHaveScreenshot(`${name}-${theme}.png`, {
          fullPage: true,
        });
      });
    }

    for (const { name, path, maskSelector } of ADMIN_ROUTES) {
      test(name, async ({ page }) => {
        await setTheme(page, theme);
        await login(page);
        await page.goto(path);
        await page.waitForLoadState("networkidle");
        await expect(page).toHaveScreenshot(`${name}-${theme}.png`, {
          fullPage: true,
          mask: [page.locator(maskSelector)],
        });
      });
    }
  });
}

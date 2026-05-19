// Screenshot baselines for every top-level route, light + dark.
//
// First-time run:   `pnpm test:e2e:update` to capture baselines on your host.
// Subsequent runs:  `pnpm test:e2e` validates diffs are within tolerance.
//
// Tolerance is set in playwright.config.ts (maxDiffPixelRatio: 0.02) because
// font rendering varies subtly between machines and OSes.

import { expect, test } from "@playwright/test";
import { login, setTheme } from "./helpers";

const ROUTES = [
  { name: "dashboard", path: "/" },
  { name: "wiki-cvs", path: "/wiki/cvs" },
  { name: "wiki-experiences", path: "/wiki/experiences" },
  { name: "applications", path: "/applications" },
  { name: "settings", path: "/settings" },
  { name: "admin-users", path: "/admin/users" },
  { name: "admin-llm-keys", path: "/admin/llm-keys" },
];

for (const theme of ["light", "dark"] as const) {
  test.describe(`screenshots — ${theme}`, () => {
    test("login page", async ({ page }) => {
      await setTheme(page, theme);
      await page.goto("/login");
      await expect(page.getByText("Sign in")).toBeVisible();
      await expect(page).toHaveScreenshot(`login-${theme}.png`, { fullPage: true });
    });

    for (const { name, path } of ROUTES) {
      test(name, async ({ page }) => {
        await setTheme(page, theme);
        await login(page);
        await page.goto(path);
        // Wait until the heading appears so async data has rendered.
        await page.waitForLoadState("networkidle");
        await expect(page).toHaveScreenshot(`${name}-${theme}.png`, {
          fullPage: true,
        });
      });
    }
  });
}

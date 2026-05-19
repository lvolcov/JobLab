// Shared helpers for joblab e2e tests.

import type { Page } from "@playwright/test";

export const ADMIN_EMAIL = "admin@example.com";
export const ADMIN_PASSWORD = "change_me_on_first_login";

/** Log in via the UI and wait for the dashboard. */
export async function login(
  page: Page,
  email = ADMIN_EMAIL,
  password = ADMIN_PASSWORD,
): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL("**/");
}

/** Force a specific theme regardless of prior localStorage. */
export async function setTheme(page: Page, mode: "light" | "dark"): Promise<void> {
  await page.addInitScript((m) => {
    window.localStorage.setItem("joblab.theme", m as string);
  }, mode);
}

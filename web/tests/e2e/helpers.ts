// Shared helpers for joblab e2e tests.
//
// Test isolation: most tests use `createTestUser` to spin up a fresh,
// disposable account via the admin API. That way the suite never depends on
// pre-existing DB state and never needs the DB to be reset. Only the seeded
// admin (`admin@example.com`) is assumed to exist — that is the project's
// baseline account, not test data.

import type { APIRequestContext, Page } from "@playwright/test";

export const ADMIN_EMAIL = "admin@example.com";
export const ADMIN_PASSWORD = "change_me_on_first_login";
export const API_BASE = process.env.JOBLAB_API_URL ?? "http://localhost:8010";

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

/** Get the CSRF cookie value from an APIRequestContext (must be logged in). */
async function csrfFor(request: APIRequestContext): Promise<string> {
  const state = await request.storageState();
  const cookie = state.cookies.find((c) => c.name === "joblab_csrf");
  if (!cookie) throw new Error("no joblab_csrf cookie — login first");
  return cookie.value;
}

/** Log into the admin account via the API and return its CSRF token. */
async function loginAdminApi(request: APIRequestContext): Promise<string> {
  await request.post(`${API_BASE}/auth/login`, {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  return csrfFor(request);
}

export interface TestUser {
  email: string;
  password: string;
}

/**
 * Create a unique, throwaway user via the admin API and log into it through
 * the UI. Returns the user's credentials so individual tests can re-login if
 * they need to.
 */
export async function createTestUser(page: Page): Promise<TestUser> {
  // Use a separate API context so admin cookies don't bleed into the page.
  const adminApi = await page.request;
  const csrf = await loginAdminApi(adminApi);

  const email = `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
  const password = "e2e_pw_test_123";

  const res = await adminApi.post(`${API_BASE}/admin/users`, {
    headers: { "x-csrf-token": csrf },
    data: { email, password, is_superuser: false },
  });
  if (!res.ok()) {
    throw new Error(`createTestUser failed: ${res.status()} ${await res.text()}`);
  }

  // Clear cookies (admin session) and log into the new user via the UI.
  await page.context().clearCookies();
  await login(page, email, password);
  return { email, password };
}

// Generation with the TEST_MODE stub adapter — exercises the full UI flow.
// Each test creates its own user + application so runs never depend on prior
// state or each other.

import { expect, test } from "@playwright/test";
import { createTestUser } from "./helpers";

async function addPersonalKey(page: import("@playwright/test").Page) {
  await page.goto("/settings");
  await page.getByLabel(/Label/i).fill("e2e key");
  await page.getByLabel(/API key/i).fill("sk-fake-test");
  await page.getByRole("button", { name: /add key/i }).click();
  await expect(page.getByText(/e2e key/)).toBeVisible();
}

async function createApplication(
  page: import("@playwright/test").Page,
  title: string,
) {
  await page.goto("/applications");
  await page.getByRole("button", { name: /new application/i }).click();
  await page.getByLabel(/Role title \*/i).fill(title);
  await page.getByLabel(/Company/i).fill("E2E Co");
  await page.getByLabel(/Job description/i).fill("Build robust systems.");
  await page.getByRole("button", { name: /^Create$/i }).click();
  await page.getByRole("link", { name: title }).click();
}

test("create application, add personal key, generate a CV", async ({ page }) => {
  await createTestUser(page);
  await addPersonalKey(page);
  await createApplication(page, `E2E Engineer ${Date.now()}`);

  await page.getByRole("button", { name: /^Generate$/i }).click();
  await expect(page.getByText(/Test generation output/i)).toBeVisible();
});

test("application feedback persists across reload", async ({ page }) => {
  await createTestUser(page);
  await addPersonalKey(page);
  const title = `E2E Engineer ${Date.now()}`;
  await createApplication(page, title);

  const feedback = "Recruiter said timing was off.";
  const textarea = page.getByLabel(/Feedback received/i);
  await textarea.fill(feedback);
  await page
    .locator("h2", { hasText: "Feedback & notes" })
    .locator("..")
    .getByRole("button", { name: /^Save$/i })
    .click();

  await page.reload();
  await expect(page.getByLabel(/Feedback received/i)).toHaveValue(feedback);
});

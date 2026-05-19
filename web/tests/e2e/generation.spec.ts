// Generation with the TEST_MODE stub adapter — exercises the full UI flow.

import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("create application, add personal key, generate a CV", async ({ page }) => {
  await login(page);

  // Add a personal API key (TEST_MODE will ignore the value but the resolver
  // still requires a row).
  await page.goto("/settings");
  await page.getByLabel(/Label/i).fill("e2e key");
  await page.getByLabel(/API key/i).fill("sk-fake-test");
  await page.getByRole("button", { name: /add key/i }).click();
  await expect(page.getByText(/e2e key/)).toBeVisible();

  // Create an application.
  await page.goto("/applications");
  await page.getByRole("button", { name: /new application/i }).click();
  await page.getByLabel(/Role title \*/i).fill("E2E Engineer");
  await page.getByLabel(/Company/i).fill("E2E Co");
  await page.getByLabel(/Job description/i).fill("Build robust systems.");
  await page.getByRole("button", { name: /^Create$/i }).click();
  await page.getByRole("link", { name: /E2E Engineer/ }).click();

  // Generate a CV — TEST_MODE returns canned text, never hits OpenAI.
  await page.getByRole("button", { name: /^Generate$/i }).click();
  await expect(page.getByText(/Test generation output/i)).toBeVisible();
});

test("update application feedback persists across reload", async ({ page }) => {
  await login(page);
  await page.goto("/applications");
  await page.getByRole("link", { name: /E2E Engineer/ }).first().click();

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

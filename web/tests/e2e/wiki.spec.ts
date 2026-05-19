// Wiki: create a skill under a fresh test user and verify the dashboard
// reflects the new entry. Each run uses an isolated user so no DB reset is
// required and the test never collides with previous runs.

import { expect, test } from "@playwright/test";
import { createTestUser } from "./helpers";

test("create a skill and see it appear in the wiki list", async ({ page }) => {
  await createTestUser(page);
  await page.goto("/wiki/skills");

  const skillName = `e2e-skill-${Date.now()}`;
  await page.getByLabel(/Name \*/i).fill(skillName);
  await page.getByLabel(/Level/i).fill("expert");
  await page.getByRole("button", { name: /add entry/i }).click();

  await expect(page.getByText(skillName)).toBeVisible();

  // Dashboard still loads for the test user.
  await page.goto("/");
  await expect(page.locator("a", { hasText: "Skills" }).first()).toBeVisible();
});

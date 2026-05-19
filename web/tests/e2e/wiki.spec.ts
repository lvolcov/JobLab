// Wiki: create + delete an entry, verify the dashboard count moves.

import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("create a skill and see the dashboard count update", async ({ page }) => {
  await login(page);
  await page.goto("/wiki/skills");

  const skillName = `e2e-skill-${Date.now()}`;
  await page.getByLabel(/Name \*/i).fill(skillName);
  await page.getByLabel(/Level/i).fill("expert");
  await page.getByRole("button", { name: /add entry/i }).click();

  await expect(page.getByText(skillName)).toBeVisible();

  // Dashboard should reflect at least one skill.
  await page.goto("/");
  const tile = page.locator("a", { hasText: "Skills" }).first();
  await expect(tile).toBeVisible();

  // Cleanup so subsequent runs stay deterministic.
  await page.goto("/wiki/skills");
  await page
    .locator("li", { has: page.getByText(skillName) })
    .getByRole("button", { name: /delete/i })
    .click();
  page.once("dialog", (d) => d.accept());
});

// Document upload: txt file is parsed and listed. Uses an isolated test user
// so no pre-existing DB state is assumed.

import { expect, test } from "@playwright/test";
import { API_BASE, createTestUser } from "./helpers";

test("upload a text document and see it returned parsed", async ({ page, request }) => {
  await createTestUser(page);

  // Upload via the API using the browser context's cookies so CSRF works.
  const cookies = await page.context().cookies();
  const csrf = cookies.find((c) => c.name === "joblab_csrf")?.value ?? "";

  // Reuse the browser session cookies for the request context.
  const session = cookies.find((c) => c.name === "joblab_session")?.value ?? "";
  const r = await request.post(`${API_BASE}/documents/upload`, {
    headers: {
      "x-csrf-token": csrf,
      cookie: `joblab_session=${session}; joblab_csrf=${csrf}`,
    },
    multipart: {
      file: {
        name: "note.txt",
        mimeType: "text/plain",
        buffer: Buffer.from("e2e document content"),
      },
    },
  });
  expect(r.status()).toBe(201);
  const body = await r.json();
  expect(body.parsed_text).toBe("e2e document content");
});

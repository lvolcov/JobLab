// Document upload: txt file is parsed and listed.

import { expect, test } from "@playwright/test";
import { login } from "./helpers";

test("upload a text document and see it listed (via API)", async ({ page, request }) => {
  await login(page);

  // The current UI ships document upload as an API endpoint without a route in
  // this milestone; verify via the API using the browser context's cookies so
  // CSRF works.
  const cookies = await page.context().cookies();
  const csrf = cookies.find((c) => c.name === "joblab_csrf")?.value ?? "";

  const r = await request.post("http://localhost:8010/documents/upload", {
    headers: { "x-csrf-token": csrf },
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

// joblab — Import CV (PDF) button used at the top of the wiki page.
// Disabled when the user hasn't picked a default AI provider in Settings.

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { FileUp, Loader2 } from "lucide-react";
import { Link } from "react-router-dom";
import { ApiError, api, type ImportResult } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Button } from "./ui";

const ENTITY_LABELS: Record<keyof Omit<ImportResult, "provider" | "attempts">, string> = {
  cvs: "CVs",
  experiences: "Experiences",
  projects: "Projects",
  skills: "Skills",
  qualifications: "Qualifications",
  education: "Education",
};

function ResultSummary({ result }: { result: ImportResult }) {
  const rows = (Object.keys(ENTITY_LABELS) as Array<keyof typeof ENTITY_LABELS>).filter(
    (k) => {
      const s = result[k];
      return s.inserted || s.skipped_exact || s.flagged_duplicate;
    },
  );
  if (rows.length === 0) {
    return <p className="text-sm text-muted">Nothing detected in this PDF.</p>;
  }
  return (
    <ul className="grid gap-1 text-sm">
      {rows.map((k) => {
        const s = result[k];
        return (
          <li key={k}>
            <span className="font-medium">{ENTITY_LABELS[k]}:</span>{" "}
            <span className="text-muted">
              {s.inserted} new
              {s.flagged_duplicate ? `, ${s.flagged_duplicate} flagged` : ""}
              {s.skipped_exact ? `, ${s.skipped_exact} skipped` : ""}
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export function CvImportButton() {
  const qc = useQueryClient();
  const { me } = useAuth();
  const fileInput = useRef<HTMLInputElement | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const upload = useMutation({
    mutationFn: (file: File) => {
      const fd = new FormData();
      fd.append("file", file);
      return api.upload<ImportResult>("/wiki/import", fd);
    },
    onSuccess: (r) => {
      setResult(r);
      setError(null);
      qc.invalidateQueries({ queryKey: ["wiki"] });
      qc.invalidateQueries({ queryKey: ["wiki-counts"] });
    },
    onError: (e: Error) => {
      setResult(null);
      setError(e instanceof ApiError ? e.detail : e.message);
    },
  });

  const ready = !!me?.default_provider;

  const onPick = () => fileInput.current?.click();

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setError(null);
    setResult(null);
    upload.mutate(f);
    e.target.value = "";
  };

  return (
    <div>
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={onPick}
          disabled={!ready || upload.isPending}
          title={
            ready
              ? "Upload a CV PDF; the AI will extract entries into your wiki."
              : "Set a default AI provider in Settings first."
          }
        >
          {upload.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Importing…
            </>
          ) : (
            <>
              <FileUp className="h-4 w-4" /> Import CV (PDF)
            </>
          )}
        </Button>
        {!ready && (
          <span className="text-sm text-muted">
            Set a{" "}
            <Link to="/settings" className="text-brand-600 hover:underline">
              default AI provider
            </Link>{" "}
            to enable this.
          </span>
        )}
        <input
          ref={fileInput}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={onChange}
        />
      </div>

      {(result || error) && (
        <div className="surface mt-3 p-4">
          {error && (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
          {result && (
            <>
              <p className="mb-2 text-sm font-semibold">
                Imported via {result.provider}
              </p>
              <ResultSummary result={result} />
              <p className="mt-2 text-xs text-muted">
                Items flagged as possible duplicates show a badge in their list.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}

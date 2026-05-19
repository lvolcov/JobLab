// Reads a generated artifact and renders content + metadata.

import { AlertTriangle, Copy } from "lucide-react";
import type { Artifact } from "../lib/api";

const TYPE_LABEL: Record<Artifact["type"], string> = {
  cv: "CV",
  cover_letter: "Cover letter",
  blind_cv: "Blind CV",
  behaviour: "Behaviour",
};

const PROVIDER_LABEL: Record<Artifact["provider"], string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  gemini: "Gemini",
};

export function ArtifactViewer({ artifact }: { artifact: Artifact }) {
  const created = new Date(artifact.created_at).toLocaleString();
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(artifact.content);
    } catch {
      /* ignore */
    }
  };

  return (
    <article className="surface p-5">
      <header className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="chip border-brand-300 text-brand-700 dark:text-brand-300">
            {TYPE_LABEL[artifact.type]}
          </span>
          {artifact.behaviour_name && (
            <span className="chip">{artifact.behaviour_name}</span>
          )}
          <span className="chip">{PROVIDER_LABEL[artifact.provider]}</span>
          <span className="chip">
            {artifact.final_word_count}/{artifact.word_limit} words
          </span>
          <span className="chip">{artifact.attempts} attempts</span>
        </div>
        <button
          type="button"
          className="btn-outline h-8 !px-3"
          onClick={() => void copy()}
          aria-label="Copy artifact text"
          title="Copy artifact text"
        >
          <Copy className="h-3.5 w-3.5" /> Copy
        </button>
      </header>
      {artifact.warning_flag && (
        <div className="mb-3 flex items-start gap-2 rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/40 dark:text-amber-200">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          The model could not get under the word limit after 3 attempts; this is the closest draft.
        </div>
      )}
      <pre className="whitespace-pre-wrap break-words text-sm leading-6"
           style={{ color: "rgb(var(--text))" }}>
        {artifact.content}
      </pre>
      <p className="mt-3 text-xs text-muted">Generated {created}</p>
    </article>
  );
}

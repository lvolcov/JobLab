// Settings — manage one's own LLM keys. Assigned global keys also shown.

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Plus, ShieldCheck, Trash2 } from "lucide-react";
import {
  Button,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Select,
  Spinner,
} from "../../components/ui";
import { api, type LLMKey, type LLMProvider } from "../../lib/api";

const PROVIDERS: LLMProvider[] = ["openai", "anthropic", "gemini"];

export default function SettingsPage() {
  const qc = useQueryClient();
  const keys = useQuery({
    queryKey: ["me-keys"],
    queryFn: () => api.get<LLMKey[]>("/me/llm-keys"),
  });

  const [form, setForm] = useState({
    provider: "openai" as LLMProvider,
    label: "",
    api_key: "",
  });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => api.post<LLMKey>("/me/llm-keys", form),
    onSuccess: () => {
      setForm({ provider: "openai", label: "", api_key: "" });
      qc.invalidateQueries({ queryKey: ["me-keys"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/me/llm-keys/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me-keys"] }),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    create.mutate();
  };

  return (
    <>
      <PageHeader
        title="My keys"
        subtitle="Add your own API keys, or use a key your admin assigned to you. Keys are encrypted at rest."
      />

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div>
          {keys.isLoading && (
            <div className="surface flex items-center justify-center p-8">
              <Spinner className="h-5 w-5 text-brand-600" />
            </div>
          )}
          {keys.data && keys.data.length === 0 && (
            <EmptyState
              title="No keys"
              description="Add a key on the right, or ask your admin to assign you a global key."
            />
          )}
          {keys.data && keys.data.length > 0 && (
            <ul className="grid gap-3">
              {keys.data.map((k) => (
                <li key={k.id} className="surface p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {k.is_global ? (
                          <ShieldCheck
                            className="h-4 w-4 text-brand-600 dark:text-brand-400"
                            aria-label="Assigned by admin"
                          />
                        ) : (
                          <KeyRound className="h-4 w-4 text-muted" />
                        )}
                        <p className="font-medium">{k.label}</p>
                      </div>
                      <p className="mt-0.5 text-sm text-muted">
                        {k.provider} • {k.is_global ? "assigned" : "personal"} • {k.masked_key}
                      </p>
                    </div>
                    {!k.is_global && (
                      <button
                        type="button"
                        className="btn-ghost h-8 !px-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                        onClick={() => {
                          if (confirm("Remove this key?")) remove.mutate(k.id);
                        }}
                        aria-label="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <aside className="surface h-fit p-5">
          <h2 className="mb-4 text-sm font-semibold">Add a personal key</h2>
          <form onSubmit={onSubmit}>
            <Field label="Provider" htmlFor="provider">
              <Select
                id="provider"
                value={form.provider}
                onChange={(e) =>
                  setForm({ ...form, provider: e.target.value as LLMProvider })
                }
              >
                {PROVIDERS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Label" htmlFor="label" hint="e.g. Personal OpenAI">
              <Input
                id="label"
                required
                value={form.label}
                onChange={(e) => setForm({ ...form, label: e.target.value })}
              />
            </Field>
            <Field
              label="API key"
              htmlFor="api_key"
              hint="Stored encrypted; never echoed back."
              error={error ?? undefined}
            >
              <Input
                id="api_key"
                required
                type="password"
                value={form.api_key}
                onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              />
            </Field>
            <Button type="submit" className="w-full" loading={create.isPending}>
              <Plus className="h-4 w-4" /> Add key
            </Button>
          </form>
        </aside>
      </section>
    </>
  );
}

// Settings — manage one's own LLM keys. Assigned global keys also shown.

import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, KeyRound, Plug, Plus, ShieldCheck, Sparkles, Trash2, XCircle } from "lucide-react";
import {
  Button,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Select,
  Spinner,
} from "../../components/ui";
import { api, type LLMKey, type LLMProvider, type Me } from "../../lib/api";
import { useAuth } from "../../lib/auth";

const PROVIDERS: LLMProvider[] = ["openai", "anthropic", "gemini"];

export default function SettingsPage() {
  const qc = useQueryClient();
  const { me, refresh: refreshMe } = useAuth();
  const keys = useQuery({
    queryKey: ["me-keys"],
    queryFn: () => api.get<LLMKey[]>("/me/llm-keys"),
  });

  const workingProviders: LLMProvider[] = Array.from(
    new Set((keys.data ?? []).map((k) => k.provider)),
  );

  const [defaultError, setDefaultError] = useState<string | null>(null);
  const setDefault = useMutation({
    mutationFn: (provider: LLMProvider | null) =>
      api.patch<Me>("/auth/me/settings", { default_provider: provider }),
    onSuccess: () => {
      setDefaultError(null);
      refreshMe();
    },
    onError: (e: Error) => setDefaultError(e.message),
  });

  // Auto-pick the first available provider when none is set yet.
  useEffect(() => {
    if (
      me &&
      me.default_provider === null &&
      workingProviders.length > 0 &&
      !setDefault.isPending
    ) {
      setDefault.mutate(workingProviders[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [me?.default_provider, workingProviders.join(",")]);

  const [form, setForm] = useState({
    provider: "openai" as LLMProvider,
    label: "",
    api_key: "",
  });
  const [error, setError] = useState<string | null>(null);

  type TestResult = { ok: boolean; detail: string };
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const testKey = useMutation({
    mutationFn: () =>
      api.post<TestResult>("/me/llm-keys/test", {
        provider: form.provider,
        api_key: form.api_key,
      }),
    onSuccess: (r) => {
      setTestResult(r);
      setError(null);
    },
    onError: (e: Error) => {
      setTestResult(null);
      setError(e.message);
    },
  });

  const create = useMutation({
    mutationFn: () => api.post<LLMKey>("/me/llm-keys", form),
    onSuccess: () => {
      setForm({ provider: "openai", label: "", api_key: "" });
      setTestResult(null);
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
        title="Settings"
        subtitle="Pick the AI used for CV imports and manage your API keys."
      />

      <section className="surface mb-6 p-5">
        <div className="mb-3 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-400" />
          <h2 className="text-sm font-semibold">Default AI provider</h2>
        </div>
        <p className="mb-3 text-sm text-muted">
          Used when you import a CV PDF on the wiki page. Only providers with a
          working key (yours or assigned) are selectable.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Select
            aria-label="Default provider"
            value={me?.default_provider ?? ""}
            disabled={workingProviders.length === 0 || setDefault.isPending}
            onChange={(e) => {
              const v = e.target.value;
              setDefault.mutate(v === "" ? null : (v as LLMProvider));
            }}
          >
            <option value="">— none —</option>
            {workingProviders.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </Select>
          {workingProviders.length === 0 && (
            <span className="text-sm text-muted">
              Add a key below first.
            </span>
          )}
          {setDefault.isPending && <Spinner className="h-4 w-4 text-brand-600" />}
        </div>
        {defaultError && (
          <p className="mt-2 text-sm text-red-600 dark:text-red-400">
            {defaultError}
          </p>
        )}
      </section>

      <h2 className="mb-3 text-base font-semibold">My keys</h2>

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
                onChange={(e) => {
                  setForm({ ...form, provider: e.target.value as LLMProvider });
                  setTestResult(null);
                }}
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
                onChange={(e) => {
                  setForm({ ...form, api_key: e.target.value });
                  setTestResult(null);
                }}
              />
            </Field>
            {testResult && (
              <div
                className={
                  "mb-3 flex items-start gap-2 rounded-lg p-2 text-sm " +
                  (testResult.ok
                    ? "bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300"
                    : "bg-red-50 text-red-800 dark:bg-red-950/30 dark:text-red-300")
                }
              >
                {testResult.ok ? (
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
                ) : (
                  <XCircle className="mt-0.5 h-4 w-4 shrink-0" />
                )}
                <span className="break-words">
                  {testResult.ok ? "Key works." : testResult.detail || "Test failed."}
                </span>
              </div>
            )}
            <div className="grid grid-cols-2 gap-2">
              <Button
                type="button"
                variant="outline"
                className="w-full"
                disabled={!form.api_key || create.isPending}
                loading={testKey.isPending}
                onClick={() => testKey.mutate()}
              >
                <Plug className="h-4 w-4" /> Test
              </Button>
              <Button
                type="submit"
                className="w-full"
                disabled={!form.label || !form.api_key}
                loading={create.isPending}
              >
                <Plus className="h-4 w-4" /> Add key
              </Button>
            </div>
          </form>
        </aside>
      </section>
    </>
  );
}

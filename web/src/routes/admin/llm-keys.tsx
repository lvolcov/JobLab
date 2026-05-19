// Admin → global LLM keys. Create, mark premium-only, test, delete.

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Crown,
  Plug,
  Plus,
  ShieldCheck,
  Trash2,
  XCircle,
} from "lucide-react";
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

type TestResult = { ok: boolean; detail: string };

export default function AdminLLMKeysPage() {
  const qc = useQueryClient();
  const keys = useQuery({
    queryKey: ["admin-llm-keys"],
    queryFn: () => api.get<LLMKey[]>("/admin/llm-keys"),
  });

  const [form, setForm] = useState({
    provider: "openai" as LLMProvider,
    label: "",
    api_key: "",
    is_premium_only: false,
  });
  const [error, setError] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<TestResult | null>(null);

  const testKey = useMutation({
    mutationFn: () =>
      api.post<TestResult>("/admin/llm-keys/test", {
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
    mutationFn: () => api.post<LLMKey>("/admin/llm-keys", form),
    onSuccess: () => {
      setForm({ provider: "openai", label: "", api_key: "", is_premium_only: false });
      setTestResult(null);
      qc.invalidateQueries({ queryKey: ["admin-llm-keys"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/llm-keys/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-llm-keys"] }),
  });

  const togglePremium = useMutation({
    mutationFn: ({ id, value }: { id: string; value: boolean }) =>
      api.patch<LLMKey>(`/admin/llm-keys/${id}`, { is_premium_only: value }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-llm-keys"] }),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    create.mutate();
  };

  return (
    <>
      <PageHeader
        title="Global LLM keys"
        subtitle="Keys available to all users. Mark a key as premium to restrict it to premium users only."
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
              title="No global keys"
              description="Add one on the right. By default it's available to every user."
            />
          )}
          {keys.data && keys.data.length > 0 && (
            <ul className="grid gap-3">
              {keys.data.map((k) => (
                <li key={k.id} className="surface p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {k.is_premium_only ? (
                          <Crown className="h-4 w-4 text-amber-500" />
                        ) : (
                          <ShieldCheck className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                        )}
                        <p className="font-medium">{k.label}</p>
                        {k.is_premium_only && (
                          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                            Premium only
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 text-sm text-muted">
                        {k.provider} • {k.masked_key}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <label className="flex cursor-pointer items-center gap-1 text-xs text-muted">
                        <input
                          type="checkbox"
                          checked={k.is_premium_only}
                          onChange={(e) =>
                            togglePremium.mutate({ id: k.id, value: e.target.checked })
                          }
                        />
                        Premium
                      </label>
                      <button
                        type="button"
                        className="btn-ghost h-8 !px-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                        onClick={() => {
                          if (confirm("Delete this global key?")) remove.mutate(k.id);
                        }}
                        aria-label="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <aside className="surface h-fit p-5">
          <h2 className="mb-4 text-sm font-semibold">New global key</h2>
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
            <Field label="Label" htmlFor="label" hint="e.g. Team OpenAI">
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
            <label className="mb-3 flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={form.is_premium_only}
                onChange={(e) =>
                  setForm({ ...form, is_premium_only: e.target.checked })
                }
              />
              <Crown className="h-4 w-4 text-amber-500" />
              Premium users only
            </label>
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

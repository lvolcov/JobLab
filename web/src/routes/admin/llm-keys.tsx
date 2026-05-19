// Admin → global LLM keys. Create, assign to users, delete.

import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, UserPlus } from "lucide-react";
import {
  Button,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Select,
  Spinner,
} from "../../components/ui";
import { api, type AppUser, type LLMKey, type LLMProvider } from "../../lib/api";

const PROVIDERS: LLMProvider[] = ["openai", "anthropic", "gemini"];

export default function AdminLLMKeysPage() {
  const qc = useQueryClient();
  const keys = useQuery({
    queryKey: ["admin-llm-keys"],
    queryFn: () => api.get<LLMKey[]>("/admin/llm-keys"),
  });
  const users = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get<AppUser[]>("/admin/users"),
  });

  const [form, setForm] = useState({
    provider: "openai" as LLMProvider,
    label: "",
    api_key: "",
  });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => api.post<LLMKey>("/admin/llm-keys", form),
    onSuccess: () => {
      setForm({ provider: "openai", label: "", api_key: "" });
      qc.invalidateQueries({ queryKey: ["admin-llm-keys"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/llm-keys/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-llm-keys"] }),
  });

  const assign = useMutation({
    mutationFn: ({ keyId, userId }: { keyId: string; userId: string }) =>
      api.post(`/admin/llm-keys/${keyId}/assign`, { user_id: userId }),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    create.mutate();
  };

  const userOpts = useMemo(() => users.data ?? [], [users.data]);

  return (
    <>
      <PageHeader
        title="Global LLM keys"
        subtitle="Keys you provide for assigned users. Assignments listed per key."
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
              description="Add one on the right to share across selected users."
            />
          )}
          {keys.data && keys.data.length > 0 && (
            <ul className="grid gap-3">
              {keys.data.map((k) => (
                <li key={k.id} className="surface p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{k.label}</p>
                      <p className="text-sm text-muted">
                        {k.provider} • {k.masked_key}
                      </p>
                    </div>
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
                  <div className="mt-4 flex flex-wrap items-end gap-2">
                    <Field label="Assign to user" htmlFor={`assign-${k.id}`}>
                      <Select id={`assign-${k.id}`} defaultValue="">
                        <option value="" disabled>
                          Select user…
                        </option>
                        {userOpts.map((u) => (
                          <option key={u.id} value={u.id}>
                            {u.email}
                          </option>
                        ))}
                      </Select>
                    </Field>
                    <Button
                      variant="outline"
                      className="mb-4"
                      onClick={(e) => {
                        const select = (e.currentTarget.previousElementSibling
                          ?.querySelector("select") as HTMLSelectElement | null);
                        if (select?.value) {
                          assign.mutate({ keyId: k.id, userId: select.value });
                          select.value = "";
                        }
                      }}
                    >
                      <UserPlus className="h-4 w-4" /> Assign
                    </Button>
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

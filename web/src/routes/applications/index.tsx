// Applications list — create a new one inline; click to open detail.

import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Briefcase, Plus } from "lucide-react";
import {
  Button,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Select,
  Spinner,
  Textarea,
} from "../../components/ui";
import { api, type Application } from "../../lib/api";

const STATUSES: Application["status"][] = [
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];

const STATUS_CLASS: Record<Application["status"], string> = {
  applied: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  screening: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200",
  interview: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
  offer: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200",
  rejected: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200",
  withdrawn: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
};

export default function ApplicationsPage() {
  const qc = useQueryClient();
  const apps = useQuery({
    queryKey: ["applications"],
    queryFn: () => api.get<Application[]>("/applications"),
  });

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    role_title: "",
    company: "",
    jd_text: "",
    status: "applied" as Application["status"],
  });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: (payload: typeof form) => api.post<Application>("/applications", payload),
    onSuccess: () => {
      setForm({ role_title: "", company: "", jd_text: "", status: "applied" });
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["applications"] });
      qc.invalidateQueries({ queryKey: ["applications-recent"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    create.mutate(form);
  };

  return (
    <>
      <PageHeader
        title="Applications"
        subtitle="Each role you target. Generations live inside each application."
        actions={
          <Button onClick={() => setOpen((o) => !o)}>
            <Plus className="h-4 w-4" /> New application
          </Button>
        }
      />

      {open && (
        <div className="surface mb-6 p-5">
          <h2 className="mb-4 text-sm font-semibold">New application</h2>
          <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
            <Field label="Role title *" htmlFor="role_title">
              <Input
                id="role_title"
                required
                value={form.role_title}
                onChange={(e) => setForm({ ...form, role_title: e.target.value })}
              />
            </Field>
            <Field label="Company" htmlFor="company">
              <Input
                id="company"
                value={form.company}
                onChange={(e) => setForm({ ...form, company: e.target.value })}
              />
            </Field>
            <Field label="Status" htmlFor="status">
              <Select
                id="status"
                value={form.status}
                onChange={(e) =>
                  setForm({ ...form, status: e.target.value as Application["status"] })
                }
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </Select>
            </Field>
            <div className="md:col-span-2">
              <Field
                label="Job description"
                htmlFor="jd_text"
                hint="Paste the full JD here — used by every generation."
              >
                <Textarea
                  id="jd_text"
                  rows={6}
                  value={form.jd_text}
                  onChange={(e) => setForm({ ...form, jd_text: e.target.value })}
                />
              </Field>
            </div>
            {error && (
              <p className="md:col-span-2 text-sm text-red-600 dark:text-red-400">{error}</p>
            )}
            <div className="md:col-span-2 flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Create
              </Button>
            </div>
          </form>
        </div>
      )}

      {apps.isLoading && (
        <div className="surface flex items-center justify-center p-8">
          <Spinner className="h-5 w-5 text-brand-600" />
        </div>
      )}
      {apps.data && apps.data.length === 0 && (
        <EmptyState
          title="No applications yet"
          description="Add roles you're applying for to generate tailored documents."
          action={
            <Button onClick={() => setOpen(true)}>
              <Plus className="h-4 w-4" /> New application
            </Button>
          }
        />
      )}
      {apps.data && apps.data.length > 0 && (
        <div className="surface overflow-hidden">
          <ul className="divide-y" style={{ borderColor: "rgb(var(--border))" }}>
            {apps.data.map((a) => (
              <li key={a.id}>
                <Link
                  to={`/applications/${a.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-4 transition-colors duration-150 hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-300">
                      <Briefcase className="h-4 w-4" />
                    </span>
                    <div className="min-w-0">
                      <p className="truncate font-medium">{a.role_title}</p>
                      <p className="truncate text-sm text-muted">{a.company || "—"}</p>
                      {a.jd_text && (
                        <p className="mt-0.5 line-clamp-2 text-xs text-muted opacity-75">
                          {a.jd_text.replace(/\s+/g, " ").slice(0, 200)}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className={`chip shrink-0 border-transparent ${STATUS_CLASS[a.status]}`}>
                    {a.status}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}

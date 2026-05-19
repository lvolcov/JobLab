// Generic wiki entity page (list + create + inline edit + delete).
// Driven by per-entity field configs so the same component handles all six.

import { useState, type FormEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Pencil, Plus, Trash2, X } from "lucide-react";
import {
  Button,
  EmptyState,
  Field,
  Input,
  Spinner,
  Textarea,
} from "../../components/ui";
import { api, type WikiBaseRow } from "../../lib/api";

type FieldType = "text" | "textarea" | "date";

interface FieldDef {
  name: string;
  label: string;
  type: FieldType;
  required?: boolean;
  hint?: string;
}

interface EntityConfig {
  title: string;
  primary: string; // field used as row title
  secondary?: string; // optional second-line label
  fields: FieldDef[];
}

const CONFIGS: Record<string, EntityConfig> = {
  cvs: {
    title: "CVs",
    primary: "title",
    fields: [
      { name: "title", label: "Title", type: "text", required: true },
      { name: "body_md", label: "Body (Markdown)", type: "textarea" },
    ],
  },
  experiences: {
    title: "Experiences",
    primary: "title",
    secondary: "employer",
    fields: [
      { name: "title", label: "Title", type: "text", required: true },
      { name: "employer", label: "Employer", type: "text", required: true },
      { name: "start", label: "Start", type: "date" },
      { name: "end", label: "End", type: "date" },
      { name: "summary", label: "Summary", type: "textarea" },
      { name: "achievements", label: "Achievements", type: "textarea" },
    ],
  },
  projects: {
    title: "Projects",
    primary: "name",
    secondary: "role",
    fields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "role", label: "Role", type: "text" },
      { name: "start", label: "Start", type: "date" },
      { name: "end", label: "End", type: "date" },
      { name: "summary", label: "Summary", type: "textarea" },
      { name: "achievements", label: "Achievements", type: "textarea" },
    ],
  },
  skills: {
    title: "Skills",
    primary: "name",
    secondary: "level",
    fields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "level", label: "Level", type: "text", hint: "e.g. beginner, expert" },
      { name: "notes", label: "Notes", type: "textarea" },
    ],
  },
  qualifications: {
    title: "Qualifications",
    primary: "name",
    secondary: "issuer",
    fields: [
      { name: "name", label: "Name", type: "text", required: true },
      { name: "issuer", label: "Issuer", type: "text" },
      { name: "date_awarded", label: "Date awarded", type: "date" },
      { name: "details", label: "Details", type: "textarea" },
    ],
  },
  education: {
    title: "Education",
    primary: "qualification",
    secondary: "institution",
    fields: [
      { name: "qualification", label: "Qualification", type: "text", required: true },
      { name: "institution", label: "Institution", type: "text", required: true },
      { name: "start", label: "Start", type: "date" },
      { name: "end", label: "End", type: "date" },
      { name: "details", label: "Details", type: "textarea" },
    ],
  },
};

function emptyForm(cfg: EntityConfig): Record<string, string> {
  return Object.fromEntries(cfg.fields.map((f) => [f.name, ""]));
}

export default function WikiEntityPage() {
  const { entity } = useParams<{ entity: string }>();
  const navigate = useNavigate();
  const cfg = entity ? CONFIGS[entity] : undefined;

  if (!cfg) {
    navigate("/wiki/cvs", { replace: true });
    return null;
  }
  return <WikiEntityInner entity={entity!} cfg={cfg} key={entity} />;
}

function WikiEntityInner({ entity, cfg }: { entity: string; cfg: EntityConfig }) {
  const path = `/wiki/${entity}`;
  const qc = useQueryClient();

  const list = useQuery({
    queryKey: ["wiki", entity],
    queryFn: () => api.get<WikiBaseRow[]>(path),
  });

  const [form, setForm] = useState<Record<string, string>>(() => emptyForm(cfg));
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api.post<WikiBaseRow>(path, payload),
    onSuccess: () => {
      setForm(emptyForm(cfg));
      setEditingId(null);
      qc.invalidateQueries({ queryKey: ["wiki", entity] });
      qc.invalidateQueries({ queryKey: ["wiki-counts"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      api.patch<WikiBaseRow>(`${path}/${id}`, payload),
    onSuccess: () => {
      setForm(emptyForm(cfg));
      setEditingId(null);
      qc.invalidateQueries({ queryKey: ["wiki", entity] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`${path}/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["wiki", entity] });
      qc.invalidateQueries({ queryKey: ["wiki-counts"] });
    },
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    const payload: Record<string, unknown> = {};
    for (const f of cfg.fields) {
      const v = form[f.name] ?? "";
      if (f.type === "date") payload[f.name] = v || null;
      else payload[f.name] = v;
    }
    if (editingId) {
      update.mutate({ id: editingId, payload });
    } else {
      create.mutate(payload);
    }
  };

  const startEdit = (row: WikiBaseRow) => {
    const next = emptyForm(cfg);
    for (const f of cfg.fields) {
      const raw = row[f.name];
      next[f.name] = raw == null ? "" : String(raw);
    }
    setForm(next);
    setEditingId(row.id);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const cancelEdit = () => {
    setForm(emptyForm(cfg));
    setEditingId(null);
    setError(null);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <section>
        {list.isLoading && (
          <div className="surface flex items-center justify-center p-8">
            <Spinner className="h-5 w-5 text-brand-600" />
          </div>
        )}
        {list.data && list.data.length === 0 && (
          <EmptyState
            title={`No ${cfg.title.toLowerCase()} yet`}
            description="Add your first entry using the form on the right."
          />
        )}
        {list.data && list.data.length > 0 && (
          <ul className="grid gap-3">
            {list.data.map((row) => (
              <li key={row.id} className="surface p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="truncate font-medium">
                        {String(row[cfg.primary] ?? "—")}
                      </p>
                      {row.possible_duplicate_of_id && (
                        <span
                          title="An AI import flagged this as a likely duplicate of an existing entry."
                          className="inline-flex shrink-0 items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950/40 dark:text-amber-300"
                        >
                          <AlertTriangle className="h-3 w-3" />
                          Possible duplicate
                        </span>
                      )}
                    </div>
                    {cfg.secondary && (
                      <p className="truncate text-sm text-muted">
                        {String(row[cfg.secondary] ?? "")}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-1">
                    <button
                      type="button"
                      className="btn-ghost h-8 !px-2"
                      onClick={() => startEdit(row)}
                      aria-label="Edit"
                      title="Edit"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      type="button"
                      className="btn-ghost h-8 !px-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                      onClick={() => {
                        if (confirm("Delete this entry?")) remove.mutate(row.id);
                      }}
                      aria-label="Delete"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <aside className="surface h-fit p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold">
            {editingId ? "Edit entry" : "New entry"}
          </h2>
          {editingId && (
            <button
              type="button"
              className="btn-ghost h-7 !px-2"
              onClick={cancelEdit}
              aria-label="Cancel edit"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <form onSubmit={onSubmit}>
          {cfg.fields.map((f) => (
            <Field key={f.name} label={f.label + (f.required ? " *" : "")} htmlFor={f.name} hint={f.hint}>
              {f.type === "textarea" ? (
                <Textarea
                  id={f.name}
                  rows={3}
                  value={form[f.name]}
                  onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}
                  required={f.required}
                />
              ) : (
                <Input
                  id={f.name}
                  type={f.type}
                  value={form[f.name]}
                  onChange={(e) => setForm({ ...form, [f.name]: e.target.value })}
                  required={f.required}
                />
              )}
            </Field>
          ))}
          {error && (
            <p className="mb-3 text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
          <Button
            type="submit"
            className="w-full"
            loading={create.isPending || update.isPending}
          >
            {editingId ? (
              "Save changes"
            ) : (
              <span className="inline-flex items-center gap-2">
                <Plus className="h-4 w-4" /> Add entry
              </span>
            )}
          </Button>
        </form>
      </aside>
    </div>
  );
}

// Application detail — editable metadata + generator form + artifact list.

import { useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Sparkles, Trash2 } from "lucide-react";
import { ArtifactViewer } from "../../components/ArtifactViewer";
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
import {
  api,
  ApiError,
  type Application,
  type Artifact,
  type ArtifactType,
  type LLMKey,
  type LLMProvider,
} from "../../lib/api";

const STATUSES: Application["status"][] = [
  "applied",
  "screening",
  "interview",
  "offer",
  "rejected",
  "withdrawn",
];

const TYPE_OPTIONS: { value: ArtifactType; label: string }[] = [
  { value: "cv", label: "CV" },
  { value: "cover_letter", label: "Cover letter" },
  { value: "blind_cv", label: "Blind CV (UK Civil Service)" },
  { value: "behaviour", label: "Behaviour (STAR, UK Civil Service)" },
];

const DEFAULT_LIMITS: Record<ArtifactType, number> = {
  cv: 800,
  cover_letter: 400,
  blind_cv: 800,
  behaviour: 250,
};

export default function ApplicationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const appQ = useQuery({
    queryKey: ["application", id],
    queryFn: () => api.get<Application>(`/applications/${id}`),
    enabled: !!id,
  });

  const artifactsQ = useQuery({
    queryKey: ["artifacts", id],
    queryFn: () => api.get<Artifact[]>(`/applications/${id}/artifacts`),
    enabled: !!id,
  });

  const keysQ = useQuery({
    queryKey: ["me-keys"],
    queryFn: () => api.get<LLMKey[]>("/me/llm-keys"),
  });

  const update = useMutation({
    mutationFn: (patch: Partial<Application>) =>
      api.patch<Application>(`/applications/${id}`, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["application", id] }),
  });

  const remove = useMutation({
    mutationFn: () => api.delete(`/applications/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
      navigate("/applications", { replace: true });
    },
  });

  if (!id) return null;

  if (appQ.isLoading || !appQ.data) {
    return (
      <div className="grid place-items-center p-8">
        <Spinner className="h-5 w-5 text-brand-600" />
      </div>
    );
  }
  const app = appQ.data;

  return (
    <>
      <Link to="/applications" className="link mb-3 inline-flex items-center gap-1 text-sm">
        <ArrowLeft className="h-3.5 w-3.5" /> All applications
      </Link>
      <PageHeader
        title={app.role_title || "Untitled application"}
        subtitle={app.company || "—"}
        actions={
          <Button
            variant="danger"
            onClick={() => {
              if (confirm("Delete this application and all artifacts?")) remove.mutate();
            }}
          >
            <Trash2 className="h-4 w-4" /> Delete
          </Button>
        }
      />

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="grid gap-6">
          <MetadataCard app={app} onSave={(p) => update.mutate(p)} saving={update.isPending} />

          <GeneratorCard
            appId={id}
            providersAvailable={keysQ.data ?? []}
            onCreated={(art) => {
              qc.setQueryData<Artifact[]>(["artifacts", id], (prev) =>
                prev ? [art, ...prev] : [art],
              );
            }}
          />

          <section>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
              Generated artifacts
            </h2>
            {artifactsQ.isLoading && (
              <div className="surface flex items-center justify-center p-8">
                <Spinner className="h-5 w-5 text-brand-600" />
              </div>
            )}
            {artifactsQ.data && artifactsQ.data.length === 0 && (
              <EmptyState
                title="No generations yet"
                description="Pick a document type above and click Generate."
              />
            )}
            {artifactsQ.data && artifactsQ.data.length > 0 && (
              <div className="grid gap-4">
                {artifactsQ.data.map((a) => (
                  <ArtifactViewer key={a.id} artifact={a} />
                ))}
              </div>
            )}
          </section>
        </div>

        <FeedbackCard app={app} onSave={(p) => update.mutate(p)} saving={update.isPending} />
      </section>
    </>
  );
}

// ---------- subcomponents ----------

function MetadataCard({
  app,
  onSave,
  saving,
}: {
  app: Application;
  onSave: (p: Partial<Application>) => void;
  saving: boolean;
}) {
  const [form, setForm] = useState({
    role_title: app.role_title,
    company: app.company,
    status: app.status,
    jd_text: app.jd_text,
  });

  const dirty =
    form.role_title !== app.role_title ||
    form.company !== app.company ||
    form.status !== app.status ||
    form.jd_text !== app.jd_text;

  return (
    <div className="surface p-5">
      <h2 className="mb-4 text-sm font-semibold">Role details</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Role title" htmlFor="role_title">
          <Input
            id="role_title"
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
          <Field label="Job description" htmlFor="jd_text">
            <Textarea
              id="jd_text"
              rows={6}
              value={form.jd_text}
              onChange={(e) => setForm({ ...form, jd_text: e.target.value })}
            />
          </Field>
        </div>
      </div>
      <div className="flex justify-end">
        <Button disabled={!dirty} loading={saving} onClick={() => onSave(form)}>
          Save changes
        </Button>
      </div>
    </div>
  );
}

function FeedbackCard({
  app,
  onSave,
  saving,
}: {
  app: Application;
  onSave: (p: Partial<Application>) => void;
  saving: boolean;
}) {
  const [feedback, setFeedback] = useState(app.feedback);
  const [notes, setNotes] = useState(app.notes);
  const dirty = feedback !== app.feedback || notes !== app.notes;

  return (
    <div className="surface h-fit p-5">
      <h2 className="mb-4 text-sm font-semibold">Feedback & notes</h2>
      <Field label="Feedback received" htmlFor="feedback" hint="From recruiter, interviewer, etc.">
        <Textarea
          id="feedback"
          rows={4}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
        />
      </Field>
      <Field label="Personal notes" htmlFor="notes">
        <Textarea
          id="notes"
          rows={4}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </Field>
      <Button
        disabled={!dirty}
        loading={saving}
        onClick={() => onSave({ feedback, notes })}
        className="w-full"
      >
        Save
      </Button>
    </div>
  );
}

function GeneratorCard({
  appId,
  providersAvailable,
  onCreated,
}: {
  appId: string;
  providersAvailable: LLMKey[];
  onCreated: (a: Artifact) => void;
}) {
  const providers = useMemo(() => {
    const set = new Set<LLMProvider>();
    providersAvailable.forEach((k) => set.add(k.provider));
    return Array.from(set);
  }, [providersAvailable]);

  const [type, setType] = useState<ArtifactType>("cv");
  const [provider, setProvider] = useState<LLMProvider>(providers[0] ?? "openai");
  const [wordLimit, setWordLimit] = useState<number>(DEFAULT_LIMITS["cv"]);
  const [extras, setExtras] = useState("");
  const [behaviourName, setBehaviourName] = useState("");
  const [error, setError] = useState<string | null>(null);

  // Adjust default word limit when type changes.
  const onTypeChange = (next: ArtifactType) => {
    setType(next);
    setWordLimit(DEFAULT_LIMITS[next]);
  };

  const run = useMutation({
    mutationFn: () =>
      api.post<Artifact>(`/applications/${appId}/generate`, {
        type,
        provider,
        word_limit: wordLimit,
        extra_instructions: extras,
        behaviour_name: type === "behaviour" ? behaviourName : null,
      }),
    onSuccess: (a) => {
      onCreated(a);
      setError(null);
    },
    onError: (e) => {
      setError(e instanceof ApiError ? e.detail : (e as Error).message);
    },
  });

  return (
    <div className="surface p-5">
      <div className="mb-4 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-accent-500" />
        <h2 className="text-sm font-semibold">Generate document</h2>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Type" htmlFor="gen_type">
          <Select
            id="gen_type"
            value={type}
            onChange={(e) => onTypeChange(e.target.value as ArtifactType)}
          >
            {TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field
          label="Provider"
          htmlFor="gen_provider"
          hint={providers.length === 0 ? "No API key — add one in My keys." : undefined}
        >
          <Select
            id="gen_provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value as LLMProvider)}
          >
            {(providers.length > 0 ? providers : (["openai", "anthropic", "gemini"] as LLMProvider[])).map(
              (p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ),
            )}
          </Select>
        </Field>
        <Field label="Word limit" htmlFor="gen_words">
          <Input
            id="gen_words"
            type="number"
            min={50}
            max={4000}
            value={wordLimit}
            onChange={(e) => setWordLimit(parseInt(e.target.value || "0", 10))}
          />
        </Field>
        {type === "behaviour" && (
          <Field label="Behaviour name *" htmlFor="gen_behaviour" hint="e.g. Leadership">
            <Input
              id="gen_behaviour"
              required
              value={behaviourName}
              onChange={(e) => setBehaviourName(e.target.value)}
            />
          </Field>
        )}
        <div className="md:col-span-2">
          <Field
            label="Extra instructions"
            htmlFor="gen_extras"
            hint="Anything specific you'd like the model to do or avoid."
          >
            <Textarea
              id="gen_extras"
              rows={3}
              value={extras}
              onChange={(e) => setExtras(e.target.value)}
            />
          </Field>
        </div>
      </div>
      {error && (
        <p className="mb-3 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
      <div className="flex justify-end">
        <Button
          variant="accent"
          loading={run.isPending}
          disabled={type === "behaviour" && !behaviourName.trim()}
          onClick={() => run.mutate()}
        >
          <Sparkles className="h-4 w-4" /> Generate
        </Button>
      </div>
    </div>
  );
}

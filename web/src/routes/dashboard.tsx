// Dashboard — live counts from /wiki/* + 5 most recent applications.

import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Award,
  Briefcase,
  FileText,
  FolderGit2,
  GraduationCap,
  Sparkles,
  Wrench,
  type LucideIcon,
} from "lucide-react";
import { Card, PageHeader, Spinner } from "../components/ui";
import { api, type Application } from "../lib/api";

interface WikiTile {
  key: string;
  label: string;
  path: string;
  icon: LucideIcon;
}

const TILES: WikiTile[] = [
  { key: "cvs", label: "CVs", path: "/wiki/cvs", icon: FileText },
  { key: "experiences", label: "Experiences", path: "/wiki/experiences", icon: Briefcase },
  { key: "projects", label: "Projects", path: "/wiki/projects", icon: FolderGit2 },
  { key: "skills", label: "Skills", path: "/wiki/skills", icon: Wrench },
  { key: "qualifications", label: "Qualifications", path: "/wiki/qualifications", icon: Award },
  { key: "education", label: "Education", path: "/wiki/education", icon: GraduationCap },
];

const STATUS_COLOURS: Record<Application["status"], string> = {
  applied: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  screening: "bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200",
  interview: "bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-200",
  offer: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200",
  rejected: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200",
  withdrawn: "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
};

export default function DashboardPage() {
  const counts = useQuery({
    queryKey: ["wiki-counts"],
    queryFn: async () => {
      const entries = await Promise.all(
        TILES.map(async (t) => {
          const rows = await api.get<unknown[]>(`/wiki/${t.key}`);
          return [t.key, rows.length] as const;
        }),
      );
      return Object.fromEntries(entries) as Record<string, number>;
    },
  });

  const apps = useQuery({
    queryKey: ["applications-recent"],
    queryFn: () => api.get<Application[]>("/applications"),
  });

  return (
    <>
      <PageHeader title="Dashboard" subtitle="A snapshot of your wiki and recent applications." />

      <section className="mb-8">
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted">
          Your wiki
        </h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          {TILES.map(({ key, label, path, icon: Icon }) => {
            const value =
              counts.data?.[key] ?? (counts.isLoading ? null : 0);
            return (
              <Link
                key={key}
                to={path}
                className="surface group flex flex-col gap-2 p-4 transition-colors duration-150 hover:border-brand-400 hover:bg-brand-50/40 dark:hover:bg-brand-950/20 cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <Icon className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                  <span className="text-xs text-muted">{label}</span>
                </div>
                <div className="text-2xl font-semibold tabular-nums">
                  {value === null ? <Spinner /> : value}
                </div>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="mb-4 flex items-end justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted">
          Recent applications
        </h2>
        <Link className="link text-sm" to="/applications">
          View all
        </Link>
      </section>

      {apps.isLoading && (
        <Card>
          <Spinner className="h-5 w-5 text-brand-600" />
        </Card>
      )}
      {apps.data && apps.data.length === 0 && (
        <Card>
          <div className="flex flex-col items-start gap-3">
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-950/40 dark:text-brand-300">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="font-medium">No applications yet</p>
              <p className="text-sm text-muted">
                Start tracking roles you apply to — they appear here.
              </p>
            </div>
            <Link className="btn-primary" to="/applications">
              Create application
            </Link>
          </div>
        </Card>
      )}
      {apps.data && apps.data.length > 0 && (
        <div className="surface overflow-hidden">
          <ul className="divide-y" style={{ borderColor: "rgb(var(--border))" }}>
            {apps.data.slice(0, 5).map((a) => (
              <li key={a.id}>
                <Link
                  to={`/applications/${a.id}`}
                  className="flex items-center justify-between gap-4 px-5 py-4 transition-colors duration-150 hover:bg-slate-50 dark:hover:bg-slate-800/40 cursor-pointer"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium">{a.role_title}</p>
                    <p className="truncate text-sm text-muted">
                      {a.company || "—"}
                    </p>
                  </div>
                  <span className={`chip border-transparent ${STATUS_COLOURS[a.status]}`}>
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

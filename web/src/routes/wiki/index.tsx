// Wiki index — tabs across six entities. Routes navigate to /wiki/:entity.

import { NavLink, Navigate, Outlet, useParams } from "react-router-dom";
import { PageHeader } from "../../components/ui";

interface Tab {
  key: string;
  label: string;
}

export const WIKI_TABS: Tab[] = [
  { key: "cvs", label: "CVs" },
  { key: "experiences", label: "Experiences" },
  { key: "projects", label: "Projects" },
  { key: "skills", label: "Skills" },
  { key: "qualifications", label: "Qualifications" },
  { key: "education", label: "Education" },
];

export default function WikiLayout() {
  return (
    <>
      <PageHeader
        title="Wiki"
        subtitle="Your structured career record. Fed into every AI-generated document."
      />
      <nav className="mb-6 flex flex-wrap gap-1 border-b pb-1"
           style={{ borderColor: "rgb(var(--border))" }}>
        {WIKI_TABS.map((t) => (
          <NavLink
            key={t.key}
            to={`/wiki/${t.key}`}
            className={({ isActive }) =>
              [
                "rounded-lg px-3 py-1.5 text-sm font-medium transition-colors duration-150 cursor-pointer",
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-950/40 dark:text-brand-300"
                  : "hover:bg-slate-100 dark:hover:bg-slate-800 text-muted",
              ].join(" ")
            }
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
      <Outlet />
    </>
  );
}

export function WikiIndexRedirect() {
  const params = useParams();
  if (!params.entity) {
    return <Navigate to="/wiki/cvs" replace />;
  }
  return null;
}

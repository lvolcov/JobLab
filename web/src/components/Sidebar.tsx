// Sidebar nav. Highlights the active route via NavLink.

import { NavLink } from "react-router-dom";
import {
  BookText,
  Briefcase,
  KeyRound,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useAuth } from "../lib/auth";

interface Item {
  to: string;
  label: string;
  icon: LucideIcon;
  adminOnly?: boolean;
}

const ITEMS: Item[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/wiki", label: "Wiki", icon: BookText },
  { to: "/applications", label: "Applications", icon: Briefcase },
  { to: "/settings", label: "My keys", icon: KeyRound },
  { to: "/admin/users", label: "Users", icon: Users, adminOnly: true },
  { to: "/admin/llm-keys", label: "Global keys", icon: ShieldCheck, adminOnly: true },
];

export function Sidebar() {
  const { me } = useAuth();
  const items = ITEMS.filter((i) => !i.adminOnly || me?.is_superuser);

  return (
    <aside className="hidden w-60 shrink-0 border-r p-4 md:block"
           style={{ borderColor: "rgb(var(--border))", backgroundColor: "rgb(var(--surface))" }}>
      <div className="mb-6 flex items-center gap-2 px-2">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
          <Settings className="h-4 w-4" />
        </span>
        <span className="text-lg font-semibold tracking-tight">joblab</span>
      </div>
      <nav className="flex flex-col gap-1">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              [
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium",
                "transition-colors duration-150 cursor-pointer",
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-950/40 dark:text-brand-300"
                  : "hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-200",
              ].join(" ")
            }
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

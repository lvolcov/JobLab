// Topbar — page-agnostic header strip with theme toggle + user menu.

import { LogOut } from "lucide-react";
import { useAuth } from "../lib/auth";
import { ThemeToggle } from "./ThemeToggle";

export function Topbar() {
  const { me, logout } = useAuth();
  return (
    <header
      className="sticky top-0 z-20 flex h-14 items-center justify-end gap-2 border-b px-4 backdrop-blur-md md:px-6"
      style={{
        borderColor: "rgb(var(--border))",
        backgroundColor: "rgba(var(--surface) / 0.7)",
      }}
    >
      <ThemeToggle />
      <span className="hidden text-sm text-muted sm:inline">{me?.email}</span>
      {me?.is_superuser && (
        <span className="chip border-brand-300 text-brand-700 dark:text-brand-300">admin</span>
      )}
      <button
        type="button"
        className="btn-ghost h-9 !px-3"
        onClick={() => void logout()}
        title="Sign out"
        aria-label="Sign out"
      >
        <LogOut className="h-4 w-4" />
        <span className="hidden sm:inline">Sign out</span>
      </button>
    </header>
  );
}

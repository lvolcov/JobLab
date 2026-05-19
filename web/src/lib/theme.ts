// joblab — dark mode persistence
// Persists choice in localStorage; falls back to system preference on first load.

export type Theme = "light" | "dark";

const STORAGE_KEY = "joblab.theme";

export function getStoredTheme(): Theme | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(STORAGE_KEY);
  return v === "light" || v === "dark" ? v : null;
}

export function getSystemTheme(): Theme {
  if (typeof window === "undefined") return "light";
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function getInitialTheme(): Theme {
  return getStoredTheme() ?? getSystemTheme();
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
}

export function setTheme(theme: Theme): void {
  applyTheme(theme);
  window.localStorage.setItem(STORAGE_KEY, theme);
}

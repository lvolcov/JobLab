// Theme toggle button — persists choice in localStorage.

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import { getInitialTheme, setTheme, type Theme } from "../lib/theme";

export function ThemeToggle() {
  const [theme, setLocal] = useState<Theme>(() => getInitialTheme());

  useEffect(() => {
    setTheme(theme);
  }, [theme]);

  const next: Theme = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      className="btn-ghost h-9 w-9 !px-0"
      aria-label={`Switch to ${next} mode`}
      title={`Switch to ${next} mode`}
      onClick={() => setLocal(next)}
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

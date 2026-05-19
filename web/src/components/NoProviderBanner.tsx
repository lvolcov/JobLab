// Site-wide banner shown when the user has no default AI provider set.
// Disappears on /settings since that's where it gets fixed.

import { AlertTriangle } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../lib/auth";

export function NoProviderBanner() {
  const { me } = useAuth();
  const location = useLocation();
  if (!me || me.default_provider || location.pathname.startsWith("/settings")) {
    return null;
  }
  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-200 md:px-8">
      <div className="mx-auto flex max-w-6xl items-center gap-2">
        <AlertTriangle className="h-4 w-4 shrink-0" />
        <span>
          No default AI provider set. AI features (CV import, generation) are disabled until you{" "}
          <Link
            to="/settings"
            className="font-medium underline underline-offset-2 hover:text-amber-700 dark:hover:text-amber-100"
          >
            pick a provider in Settings
          </Link>
          .
        </span>
      </div>
    </div>
  );
}

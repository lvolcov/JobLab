// Login page. Cookie-based; on success, redirect to ?from (or /).

import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { Briefcase } from "lucide-react";
import { Button, Field, Input } from "../components/ui";
import { ThemeToggle } from "../components/ThemeToggle";
import { ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";

interface LocState {
  from?: string;
}

export default function LoginPage() {
  const { me, login, loading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!loading && me) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      const from = (location.state as LocState | null)?.from ?? "/";
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Sign-in failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="grid min-h-screen grid-rows-[auto_1fr] gap-4 px-4 py-4">
      <div className="flex justify-end">
        <ThemeToggle />
      </div>
      <div className="flex items-center justify-center">
        <div className="w-full max-w-sm">
          <div className="mb-6 flex items-center gap-2">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white">
              <Briefcase className="h-5 w-5" />
            </span>
            <span className="text-xl font-semibold tracking-tight">joblab</span>
          </div>
          <div className="surface p-6">
            <h1 className="text-lg font-semibold">Sign in</h1>
            <p className="mb-5 mt-1 text-sm text-muted">
              Access your wiki, applications, and generators.
            </p>
            <form onSubmit={onSubmit}>
              <Field label="Email" htmlFor="email">
                <Input
                  id="email"
                  type="email"
                  autoComplete="username"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </Field>
              <Field label="Password" htmlFor="password" error={error ?? undefined}>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </Field>
              <Button type="submit" className="w-full" loading={submitting}>
                Sign in
              </Button>
            </form>
          </div>
          <p className="mt-4 text-center text-xs text-muted">
            Accounts are created by your administrator.
          </p>
        </div>
      </div>
    </div>
  );
}

// Protected layout. Redirects unauthenticated users to /login.

import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Sidebar } from "../components/Sidebar";
import { Topbar } from "../components/Topbar";
import { Spinner } from "../components/ui";
import { useAuth } from "../lib/auth";

export default function ProtectedLayout({ adminOnly = false }: { adminOnly?: boolean }) {
  const { me, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="grid h-full place-items-center">
        <Spinner className="h-6 w-6 text-brand-600" />
      </div>
    );
  }
  if (!me) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (adminOnly && !me.is_superuser) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="flex h-full min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 md:px-8 md:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

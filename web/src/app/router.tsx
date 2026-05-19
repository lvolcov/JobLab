// Router configuration. Keeps main.tsx small.

import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import ProtectedLayout from "../routes/layout";
import LoginPage from "../routes/login";
import DashboardPage from "../routes/dashboard";
import WikiLayout from "../routes/wiki";
import WikiEntityPage from "../routes/wiki/entity";
import ApplicationsPage from "../routes/applications";
import ApplicationDetailPage from "../routes/applications/detail";
import SettingsPage from "../routes/settings";
import AdminUsersPage from "../routes/admin/users";
import AdminLLMKeysPage from "../routes/admin/llm-keys";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        {/* Authenticated app */}
        <Route element={<ProtectedLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="wiki" element={<WikiLayout />}>
            <Route index element={<Navigate to="cvs" replace />} />
            <Route path=":entity" element={<WikiEntityPage />} />
          </Route>
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="applications/:id" element={<ApplicationDetailPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Admin-only */}
        <Route element={<ProtectedLayout adminOnly />}>
          <Route path="admin/users" element={<AdminUsersPage />} />
          <Route path="admin/llm-keys" element={<AdminLLMKeysPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

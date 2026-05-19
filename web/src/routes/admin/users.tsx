// Admin → user management. Create, toggle active/admin, reset password, delete.

import { useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Plus, Trash2 } from "lucide-react";
import {
  Button,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Spinner,
} from "../../components/ui";
import { api, type AppUser } from "../../lib/api";

export default function AdminUsersPage() {
  const qc = useQueryClient();
  const users = useQuery({
    queryKey: ["admin-users"],
    queryFn: () => api.get<AppUser[]>("/admin/users"),
  });

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ email: "", password: "", is_superuser: false });
  const [error, setError] = useState<string | null>(null);

  const create = useMutation({
    mutationFn: () => api.post<AppUser>("/admin/users", form),
    onSuccess: () => {
      setForm({ email: "", password: "", is_superuser: false });
      setOpen(false);
      qc.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (e: Error) => setError(e.message),
  });

  const update = useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: Partial<AppUser> }) =>
      api.patch<AppUser>(`/admin/users/${id}`, patch),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api.delete(`/admin/users/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-users"] }),
  });

  const reset = useMutation({
    mutationFn: ({ id, password }: { id: string; password: string }) =>
      api.post(`/admin/users/${id}/reset-password`, { new_password: password }),
  });

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    create.mutate();
  };

  return (
    <>
      <PageHeader
        title="Users"
        subtitle="Create and manage accounts. Only admins see this page."
        actions={
          <Button onClick={() => setOpen((o) => !o)}>
            <Plus className="h-4 w-4" /> New user
          </Button>
        }
      />

      {open && (
        <div className="surface mb-6 p-5">
          <h2 className="mb-4 text-sm font-semibold">New user</h2>
          <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-3">
            <Field label="Email *" htmlFor="email">
              <Input
                id="email"
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </Field>
            <Field label="Temporary password *" htmlFor="password" hint="≥ 8 chars">
              <Input
                id="password"
                type="text"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </Field>
            <Field label="Admin" htmlFor="is_super">
              <label className="flex items-center gap-2 pt-2 text-sm">
                <input
                  id="is_super"
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                  checked={form.is_superuser}
                  onChange={(e) =>
                    setForm({ ...form, is_superuser: e.target.checked })
                  }
                />
                Grant admin privileges
              </label>
            </Field>
            {error && (
              <p className="md:col-span-3 text-sm text-red-600 dark:text-red-400">{error}</p>
            )}
            <div className="md:col-span-3 flex justify-end gap-2">
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" loading={create.isPending}>
                Create
              </Button>
            </div>
          </form>
        </div>
      )}

      {users.isLoading && (
        <div className="surface flex items-center justify-center p-8">
          <Spinner className="h-5 w-5 text-brand-600" />
        </div>
      )}
      {users.data && users.data.length === 0 && (
        <EmptyState title="No users yet" description="Create your first user above." />
      )}
      {users.data && users.data.length > 0 && (
        <div className="surface overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="surface-muted">
              <tr>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Role</th>
                <th className="px-5 py-3 font-medium">Active</th>
                <th className="px-5 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y" style={{ borderColor: "rgb(var(--border))" }}>
              {users.data.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                  <td className="px-5 py-3">{u.email}</td>
                  <td className="px-5 py-3">
                    <button
                      type="button"
                      className="chip cursor-pointer hover:bg-slate-200 dark:hover:bg-slate-700"
                      onClick={() =>
                        update.mutate({
                          id: u.id,
                          patch: { is_superuser: !u.is_superuser },
                        })
                      }
                    >
                      {u.is_superuser ? "admin" : "user"}
                    </button>
                  </td>
                  <td className="px-5 py-3">
                    <label className="inline-flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                        checked={u.is_active}
                        onChange={() =>
                          update.mutate({
                            id: u.id,
                            patch: { is_active: !u.is_active },
                          })
                        }
                      />
                    </label>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex justify-end gap-1">
                      <button
                        type="button"
                        className="btn-ghost h-8 !px-2"
                        onClick={() => {
                          const pw = window.prompt(
                            `New password for ${u.email} (min 8 chars):`,
                          );
                          if (pw && pw.length >= 8) {
                            reset.mutate({ id: u.id, password: pw });
                          }
                        }}
                        title="Reset password"
                        aria-label="Reset password"
                      >
                        <KeyRound className="h-4 w-4" />
                      </button>
                      <button
                        type="button"
                        className="btn-ghost h-8 !px-2 text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                        onClick={() => {
                          if (confirm(`Delete ${u.email}?`)) remove.mutate(u.id);
                        }}
                        title="Delete user"
                        aria-label="Delete user"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

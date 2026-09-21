"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type AdminStats, type AdminUser } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AdminPage() {
  const { token, hasRole } = useAuth();
  const isAdmin = hasRole("ADMIN", "SUPER_ADMIN");
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token || !isAdmin) return;
    try {
      const [statsResult, userList] = await Promise.all([
        api.adminStats(token),
        api.adminUsers(token, query),
      ]);
      setStats(statsResult);
      setUsers(userList);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load admin data");
    }
  }, [token, isAdmin, query]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!isAdmin) {
    return (
      <WorkspacePage title="Administration" description="Restricted area.">
        <p className="card p-5 text-sm">
          This dashboard is available to university administrators only.
        </p>
      </WorkspacePage>
    );
  }

  return (
    <WorkspacePage
      title="Administration"
      description="Usage across the university, account management and system readiness."
    >
      {error ? <p className="mb-6 text-sm text-red-500">{error}</p> : null}

      {stats ? (
        <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["People", stats.users_total],
            ["Conversations", stats.conversations_total],
            ["Messages", stats.messages_total],
            ["Documents", stats.documents_total],
            ["Indexed passages", stats.document_chunks_total],
            ["Announcements", stats.announcements_total],
            ["AI provider", stats.ai_configured ? "Configured" : "Not configured"],
            ["Embeddings", stats.embeddings_configured ? "Configured" : "Not configured"],
          ].map(([label, value]) => (
            <div key={String(label)} className="card p-4">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="mt-1 text-xl font-semibold">{value}</p>
            </div>
          ))}
        </div>
      ) : null}

      <section>
        <div className="mb-3 flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold">People</h2>
          <input
            className="field w-56"
            placeholder="Search by name or email"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        <ul className="space-y-2">
          {users.map((person) => (
            <li key={person.id} className="card flex items-center justify-between gap-4 p-4">
              <div className="min-w-0">
                <p className="truncate font-medium">{person.full_name}</p>
                <p className="text-xs text-muted-foreground">
                  {person.email} · {person.role} · {person.is_active ? "active" : "suspended"}
                </p>
              </div>
              <button
                type="button"
                className="btn-ghost px-3 py-1.5 text-xs"
                onClick={async () => {
                  if (!token) return;
                  await api.setUserActive(token, person.id, !person.is_active);
                  void load();
                }}
              >
                {person.is_active ? "Suspend" : "Reactivate"}
              </button>
            </li>
          ))}
        </ul>
      </section>
    </WorkspacePage>
  );
}

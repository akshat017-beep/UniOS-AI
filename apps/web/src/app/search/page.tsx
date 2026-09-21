"use client";

import Link from "next/link";
import { useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type SearchHit } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function SearchPage() {
  const { token } = useAuth();
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(event: React.FormEvent) {
    event.preventDefault();
    if (!token || query.trim().length < 2) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.search(token, query);
      setHits(result.hits);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Search failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Search"
      description="One search across your documents, conversations, calendar and campus announcements."
    >
      <form onSubmit={run} className="mb-8 flex gap-2">
        <input
          className="field flex-1"
          placeholder="Search everything…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <button className="btn-primary px-4 py-2 text-sm" disabled={busy}>
          Search
        </button>
      </form>

      {error ? <p className="mb-6 text-sm text-red-500">{error}</p> : null}

      {hits ? (
        hits.length === 0 ? (
          <p className="text-sm text-muted-foreground">No matches.</p>
        ) : (
          <ul className="space-y-2">
            {hits.map((hit) => (
              <li key={`${hit.kind}-${hit.id}`} className="card p-4">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{hit.kind}</p>
                <Link href={hit.link} className="font-medium hover:underline">
                  {hit.title}
                </Link>
                <p className="mt-1 text-sm text-muted-foreground">{hit.snippet}</p>
              </li>
            ))}
          </ul>
        )
      ) : null}
    </WorkspacePage>
  );
}

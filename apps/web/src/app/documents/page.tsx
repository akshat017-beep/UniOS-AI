"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type Citation, type RagStatus, type UniDocument } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function DocumentsPage() {
  const { token } = useAuth();
  const [documents, setDocuments] = useState<UniDocument[]>([]);
  const [status, setStatus] = useState<RagStatus | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [query, setQuery] = useState("");
  const [citations, setCitations] = useState<Citation[] | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [list, ragStatus] = await Promise.all([api.documents(token), api.ragStatus(token)]);
      setDocuments(list);
      setStatus(ragStatus);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load documents");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function upload(file: File) {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      await api.uploadDocument(token, file);
      await load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Upload failed");
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function runSearch(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !query.trim()) return;
    setBusy(true);
    setError("");
    try {
      const result = await api.searchDocuments(token, { query });
      setCitations(result.citations);
      setWarnings(result.injection_warnings);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Search failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Documents"
      description="Upload PDFs and notes, then ask questions and get answers with the exact page cited."
    >
      {status && !status.embeddings_configured ? (
        <p className="card mb-6 border-amber-500/40 bg-amber-500/10 p-4 text-sm">{status.detail}</p>
      ) : null}
      {status?.embeddings_configured && status.provider === "hashing" ? (
        <p className="card mb-6 border-amber-500/40 bg-amber-500/10 p-4 text-sm">{status.detail}</p>
      ) : null}

      <div className="card mb-8 p-5">
        <label className="text-sm font-medium" htmlFor="file">
          Upload a PDF, text or markdown file
        </label>
        <input
          id="file"
          ref={fileInput}
          type="file"
          accept=".pdf,.txt,.md,.csv"
          disabled={busy}
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void upload(file);
          }}
          className="mt-2 block w-full text-sm"
        />
        <p className="mt-2 text-xs text-muted-foreground">
          Scanned PDFs without selectable text are rejected rather than guessed at — OCR is not
          enabled in this deployment.
        </p>
      </div>

      {error ? <p className="mb-6 text-sm text-red-500">{error}</p> : null}

      <section className="mb-10">
        <h2 className="mb-3 text-lg font-semibold">Your library</h2>
        {documents.length === 0 ? (
          <p className="text-sm text-muted-foreground">No documents yet.</p>
        ) : (
          <ul className="space-y-2">
            {documents.map((document) => (
              <li key={document.id} className="card flex items-center justify-between gap-4 p-4">
                <div className="min-w-0">
                  <p className="truncate font-medium">{document.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {document.pages} page(s) · {(document.size_bytes / 1024).toFixed(0)} KB ·{" "}
                    {document.status}
                    {document.error ? ` · ${document.error}` : ""}
                  </p>
                </div>
                <button
                  type="button"
                  className="btn-ghost px-3 py-1.5 text-sm"
                  onClick={async () => {
                    if (!token) return;
                    await api.deleteDocument(token, document.id);
                    void load();
                  }}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2 className="mb-3 text-lg font-semibold">Find a passage</h2>
        <form onSubmit={runSearch} className="flex gap-2">
          <input
            className="field flex-1"
            placeholder="e.g. deadlock detection"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button className="btn-primary px-4 py-2 text-sm" disabled={busy}>
            Search
          </button>
        </form>

        {warnings.length > 0 ? (
          <p className="card mt-4 border-amber-500/40 bg-amber-500/10 p-3 text-xs">
            These passages contain instruction-like text ({warnings.join("; ")}). It is treated as
            data and never followed.
          </p>
        ) : null}

        {citations ? (
          citations.length === 0 ? (
            <p className="mt-4 text-sm text-muted-foreground">
              Nothing matched. Try different words, or upload the document first.
            </p>
          ) : (
            <ul className="mt-4 space-y-3">
              {citations.map((citation, index) => (
                <li key={`${citation.document_id}-${index}`} className="card p-4">
                  <p className="text-xs font-medium text-muted-foreground">
                    [{index + 1}] {citation.document_title} — page {citation.page} · score{" "}
                    {citation.score.toFixed(3)}
                  </p>
                  <p className="mt-2 text-sm">{citation.snippet}</p>
                </li>
              ))}
            </ul>
          )
        ) : null}
      </section>
    </WorkspacePage>
  );
}

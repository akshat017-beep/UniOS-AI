"use client";

import { useEffect, useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type CodingStatus, type RunResult } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const STARTERS: Record<string, string> = {
  python: 'print("Hello from UniOS AI")\n',
  javascript: 'console.log("Hello from UniOS AI");\n',
};

export default function CodingPage() {
  const { token } = useAuth();
  const [status, setStatus] = useState<CodingStatus | null>(null);
  const [language, setLanguage] = useState("python");
  const [source, setSource] = useState(STARTERS.python);
  const [stdin, setStdin] = useState("");
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.codingStatus(token).then(setStatus).catch(() => undefined);
  }, [token]);

  async function run() {
    if (!token) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.runCode(token, { language, source, stdin }));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Coding workspace"
      description="Write and run small programs, then ask the coding agent to explain or fix them."
    >
      {status ? (
        <p className="card mb-6 p-4 text-xs text-muted-foreground">{status.isolation_note}</p>
      ) : null}

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          className="field w-48"
          value={language}
          onChange={(event) => {
            setLanguage(event.target.value);
            setSource(STARTERS[event.target.value] ?? "");
          }}
        >
          {(status?.languages ?? [{ id: "python", label: "Python", available: true }]).map(
            (item) => (
              <option key={item.id} value={item.id} disabled={!item.available}>
                {item.label}
                {item.available ? "" : " (not installed)"}
              </option>
            ),
          )}
        </select>
        <button type="button" className="btn-primary px-4 py-2 text-sm" onClick={run} disabled={busy}>
          {busy ? "Running…" : "Run"}
        </button>
        {status ? (
          <span className="text-xs text-muted-foreground">
            Timeout {status.timeout_seconds}s
          </span>
        ) : null}
      </div>

      <textarea
        className="field min-h-72 w-full font-mono text-sm"
        value={source}
        spellCheck={false}
        onChange={(event) => setSource(event.target.value)}
      />

      <label className="mt-4 block text-sm font-medium" htmlFor="stdin">
        Standard input (optional)
      </label>
      <textarea
        id="stdin"
        className="field mt-1 min-h-20 w-full font-mono text-sm"
        value={stdin}
        onChange={(event) => setStdin(event.target.value)}
      />

      {error ? <p className="mt-4 text-sm text-red-500">{error}</p> : null}

      {result ? (
        <section className="card mt-6 p-5">
          <p className="text-xs text-muted-foreground">
            Exit code {result.exit_code}
            {result.timed_out ? " · timed out" : ""}
          </p>
          {result.stdout ? (
            <pre className="mt-3 overflow-x-auto rounded-lg bg-muted p-3 text-sm">
              {result.stdout}
            </pre>
          ) : null}
          {result.stderr ? (
            <pre className="mt-3 overflow-x-auto rounded-lg bg-red-500/10 p-3 text-sm text-red-500">
              {result.stderr}
            </pre>
          ) : null}
        </section>
      ) : null}
    </WorkspacePage>
  );
}

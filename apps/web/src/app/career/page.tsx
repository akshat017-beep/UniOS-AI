"use client";

import { useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type GenerationResult } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const FIELDS = [
  { id: "target_role", label: "Target role", placeholder: "Backend engineer intern" },
  { id: "summary", label: "About you", placeholder: "Final-year CSE student…" },
  { id: "education", label: "Education", placeholder: "B.Tech CSE, 2022–2026, CGPA 8.6" },
  { id: "experience", label: "Experience", placeholder: "Internships, part-time work" },
  { id: "projects", label: "Projects", placeholder: "What you built and the result" },
  { id: "skills", label: "Skills", placeholder: "Python, SQL, React…" },
  { id: "achievements", label: "Achievements", placeholder: "Hackathons, awards" },
];

export default function CareerPage() {
  const { token } = useAuth();
  const [values, setValues] = useState<Record<string, string>>({ target_role: "" });
  const [result, setResult] = useState<GenerationResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function build(event: React.FormEvent) {
    event.preventDefault();
    if (!token || (values.target_role ?? "").trim().length < 2) return;
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.resume(token, values));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not build the resume");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Career"
      description="Build a resume tailored to one role. Everything you type stays in your own account."
    >
      <form onSubmit={build} className="card mb-8 space-y-4 p-5">
        {FIELDS.map((field) => (
          <div key={field.id}>
            <label className="text-sm font-medium" htmlFor={field.id}>
              {field.label}
            </label>
            {field.id === "target_role" ? (
              <input
                id={field.id}
                className="field mt-1 w-full"
                placeholder={field.placeholder}
                value={values[field.id] ?? ""}
                onChange={(event) =>
                  setValues((current) => ({ ...current, [field.id]: event.target.value }))
                }
              />
            ) : (
              <textarea
                id={field.id}
                className="field mt-1 min-h-20 w-full"
                placeholder={field.placeholder}
                value={values[field.id] ?? ""}
                onChange={(event) =>
                  setValues((current) => ({ ...current, [field.id]: event.target.value }))
                }
              />
            )}
          </div>
        ))}
        <button className="btn-primary px-4 py-2 text-sm" disabled={busy}>
          {busy ? "Writing…" : "Build resume"}
        </button>
      </form>

      {error ? <p className="mb-6 text-sm text-red-500">{error}</p> : null}

      {result ? (
        <article className="card p-5">
          <div className="mb-3 flex items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">Drafted by {result.model}</p>
            <button
              type="button"
              className="btn-ghost px-3 py-1.5 text-xs"
              onClick={() => void navigator.clipboard.writeText(result.content)}
            >
              Copy
            </button>
          </div>
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
            {result.content}
          </pre>
        </article>
      ) : null}
    </WorkspacePage>
  );
}

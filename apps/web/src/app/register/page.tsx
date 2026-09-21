"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/site-header";
import type { UserRole } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { branding } from "@/lib/branding";

const ROLES: { value: UserRole; label: string }[] = [
  { value: "STUDENT", label: "Student" },
  { value: "FACULTY", label: "Faculty" },
  { value: "CLUB", label: "Club" },
];

export default function RegisterPage() {
  const router = useRouter();
  const { register, user, loading } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<UserRole>("STUDENT");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError("Use a password of at least 8 characters.");
      return;
    }
    setSubmitting(true);
    try {
      await register({ email, password, full_name: fullName, role });
      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not create your account");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto w-full max-w-md px-5 py-16">
        <h1 className="text-2xl font-semibold tracking-tight">Create your account</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Join {branding.name} and bring your university life into one place.
        </p>

        <form onSubmit={handleSubmit} className="card mt-6 space-y-4 p-6">
          <div>
            <label htmlFor="full_name" className="text-sm font-medium">
              Full name
            </label>
            <input
              id="full_name"
              required
              autoComplete="name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              className="field mt-1"
            />
          </div>

          <div>
            <label htmlFor="email" className="text-sm font-medium">
              University email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="field mt-1"
            />
          </div>

          <div>
            <label htmlFor="password" className="text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="field mt-1"
            />
            <p className="mt-1 text-xs text-muted-foreground">At least 8 characters.</p>
          </div>

          <div>
            <label htmlFor="role" className="text-sm font-medium">
              I am a
            </label>
            <select
              id="role"
              value={role}
              onChange={(event) => setRole(event.target.value as UserRole)}
              className="field mt-1"
            >
              {ROLES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <p className="mt-1 text-xs text-muted-foreground">
              Administrator accounts are granted by your university, not self-selected.
            </p>
          </div>

          {error ? (
            <p role="alert" className="text-sm text-danger">
              {error}
            </p>
          ) : null}

          <button type="submit" disabled={submitting} className="btn-primary w-full disabled:opacity-60">
            {submitting ? "Creating account…" : "Create account"}
          </button>

          <p className="text-center text-sm text-muted-foreground">
            Already registered?{" "}
            <Link href="/login" className="font-medium underline">
              Sign in
            </Link>
          </p>
        </form>
      </main>
    </div>
  );
}

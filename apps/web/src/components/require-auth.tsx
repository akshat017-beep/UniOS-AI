"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";
import { WorkspaceNav } from "@/components/workspace-nav";
import { useAuth } from "@/lib/auth-context";

/** Shared shell for every signed-in workspace page. */
export function WorkspacePage({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="mx-auto max-w-6xl px-5 py-16 text-muted-foreground">Loading…</main>
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-5 py-10">
      <WorkspaceNav />
      <header className="mb-8">
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </header>
      {children}
    </main>
  );
}

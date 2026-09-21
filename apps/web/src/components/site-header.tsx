"use client";

import Link from "next/link";
import { ThemeToggle } from "@/components/theme-provider";
import { branding } from "@/lib/branding";
import { useAuth } from "@/lib/auth-context";

export function SiteHeader() {
  const { user, loading, logout } = useAuth();

  return (
    <header className="sticky top-0 z-20 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="grid size-8 place-items-center rounded-lg bg-primary text-sm text-primary-foreground">
            U
          </span>
          {branding.name}
        </Link>

        <nav className="flex items-center gap-2">
          <ThemeToggle />
          {loading ? (
            <span className="text-sm text-muted-foreground">Loading…</span>
          ) : user ? (
            <>
              <Link href="/chat" className="btn-ghost px-3 py-2 text-sm">
                Assistant
              </Link>
              <Link href="/dashboard" className="btn-ghost px-3 py-2 text-sm">
                Dashboard
              </Link>
              <button type="button" onClick={() => void logout()} className="btn-primary px-3 py-2 text-sm">
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn-ghost px-3 py-2 text-sm">
                Log in
              </Link>
              <Link href="/register" className="btn-primary px-3 py-2 text-sm">
                Start using {branding.shortName}
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

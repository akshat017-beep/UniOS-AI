"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/site-header";
import { WorkspaceNav } from "@/components/workspace-nav";
import { api, type Announcement, type CalendarEvent, type UniNotification } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const quickActions = [
  { label: "Ask AI", href: "/chat" },
  { label: "Documents", href: "/documents" },
  { label: "Study", href: "/study" },
  { label: "Code", href: "/coding" },
  { label: "Research", href: "/research" },
  { label: "Career", href: "/career" },
  { label: "Calendar", href: "/calendar" },
  { label: "Campus", href: "/announcements" },
];

export default function DashboardPage() {
  const router = useRouter();
  const { user, token, loading } = useAuth();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [notifications, setNotifications] = useState<UniNotification[]>([]);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!token) return;
    void api.events(token, 7).then(setEvents).catch(() => undefined);
    void api.announcements(token).then(setAnnouncements).catch(() => undefined);
    void api.notifications(token).then(setNotifications).catch(() => undefined);
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen">
        <SiteHeader />
        <main className="mx-auto max-w-6xl px-5 py-16 text-sm text-muted-foreground">
          Loading your dashboard…
        </main>
      </div>
    );
  }

  if (!user) return null;

  const firstName = user.full_name.split(" ")[0];

  return (
    <div className="min-h-screen">
      <SiteHeader />

      <main className="mx-auto max-w-6xl px-5 py-10">
        <WorkspaceNav />
        <header>
          <h1 className="text-2xl font-semibold tracking-tight">Good to see you, {firstName}</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Signed in as {user.email} · {user.role.toLowerCase().replace("_", " ")}
          </p>
        </header>

        <section className="mt-8 grid gap-4 lg:grid-cols-3">
          <article className="card p-6 lg:col-span-2">
            <h2 className="font-semibold">Today&apos;s overview</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              The next seven days from your calendar, plus the latest announcements. Nothing is
              simulated — an empty list means nothing has been added yet.
            </p>
            <ul className="mt-4 space-y-2 text-sm">
              {events.length === 0 ? (
                <li className="rounded-lg border border-dashed p-3 text-muted-foreground">
                  Nothing scheduled this week —{" "}
                  <Link href="/calendar" className="underline">
                    add a deadline or plan a study week
                  </Link>
                  .
                </li>
              ) : (
                events.slice(0, 5).map((event) => (
                  <li key={event.id} className="rounded-lg border p-3">
                    <span className="font-medium">{event.title}</span>
                    <span className="ml-2 text-xs text-muted-foreground">
                      {new Date(event.starts_at).toLocaleString()}
                    </span>
                  </li>
                ))
              )}
              {announcements.slice(0, 3).map((announcement) => (
                <li key={announcement.id} className="rounded-lg border p-3">
                  <span className="font-medium">{announcement.title}</span>
                  <span className="ml-2 text-xs text-muted-foreground">announcement</span>
                </li>
              ))}
            </ul>
          </article>

          <article className="card p-6">
            <h2 className="font-semibold">Notifications</h2>
            {notifications.length === 0 ? (
              <p className="mt-2 text-sm text-muted-foreground">You are all caught up.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm">
                {notifications.slice(0, 5).map((notification) => (
                  <li key={notification.id} className="rounded-lg border p-3">
                    <p className="font-medium">{notification.title}</p>
                    <p className="text-xs text-muted-foreground">{notification.body}</p>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/announcements" className="btn-ghost mt-4 inline-block text-sm">
              Open campus
            </Link>
          </article>
        </section>

        <section className="mt-6">
          <h2 className="font-semibold">Quick actions</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => (
              <Link
                key={action.label}
                href={action.href}
                className="card flex items-center justify-between p-4 transition hover:border-primary"
              >
                <span className="text-sm font-medium">{action.label}</span>
                <span className="text-xs text-muted-foreground">Open</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="mt-6 grid gap-4 lg:grid-cols-2">
          <article className="card p-6">
            <h2 className="font-semibold">Academic context</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Your degree, branch, semester and interests help every agent answer in context. You can
              view, edit or clear this at any time.
            </p>
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-muted-foreground">Degree</dt>
                <dd>{user.profile?.degree ?? "Not set"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Branch</dt>
                <dd>{user.profile?.branch ?? "Not set"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Semester</dt>
                <dd>{user.profile?.semester ?? "Not set"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Department</dt>
                <dd>{user.profile?.department ?? "Not set"}</dd>
              </div>
            </dl>
          </article>

          <article className="card p-6">
            <h2 className="font-semibold">What you can do</h2>
            <ol className="mt-3 space-y-2 text-sm text-muted-foreground">
              <li>Ask anything — your question is routed to the right specialist automatically.</li>
              <li>Upload PDFs and get answers with the exact page cited.</li>
              <li>Generate notes and quizzes, run code, draft a resume and plan your week.</li>
            </ol>
            <Link href="/" className="btn-ghost mt-4 text-sm">
              Back to overview
            </Link>
          </article>
        </section>
      </main>
    </div>
  );
}

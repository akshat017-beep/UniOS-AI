"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type CalendarEvent, type PlannedItem } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

function formatDate(value: string) {
  return new Date(value).toLocaleString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function CalendarPage() {
  const { token } = useAuth();
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [title, setTitle] = useState("");
  const [startsAt, setStartsAt] = useState("");
  const [goal, setGoal] = useState("");
  const [days, setDays] = useState(7);
  const [hours, setHours] = useState(2);
  const [plan, setPlan] = useState<PlannedItem[] | null>(null);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setEvents(await api.events(token, 60));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load the calendar");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function addEvent(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !title.trim() || !startsAt) return;
    await api.createEvent(token, { title, starts_at: new Date(startsAt).toISOString() });
    setTitle("");
    setStartsAt("");
    void load();
  }

  async function makePlan(event: React.FormEvent) {
    event.preventDefault();
    if (!token || goal.trim().length < 3) return;
    setBusy(true);
    setError("");
    setPlan(null);
    try {
      const result = await api.planSchedule(token, {
        goal,
        days,
        hours_per_day: hours,
        save: true,
      });
      setPlan(result.items);
      setNote(result.note);
      void load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Planning failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <WorkspacePage
      title="Calendar"
      description="Keep deadlines in one place and let the assistant break a goal into daily sessions."
    >
      <div className="grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-lg font-semibold">Add something</h2>
          <form onSubmit={addEvent} className="card space-y-3 p-5">
            <input
              className="field w-full"
              placeholder="DBMS mid-term"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
            <input
              className="field w-full"
              type="datetime-local"
              value={startsAt}
              onChange={(event) => setStartsAt(event.target.value)}
            />
            <button className="btn-primary px-4 py-2 text-sm">Add to calendar</button>
          </form>

          <h2 className="mb-3 mt-8 text-lg font-semibold">Plan with AI</h2>
          <form onSubmit={makePlan} className="card space-y-3 p-5">
            <textarea
              className="field min-h-20 w-full"
              placeholder="Revise operating systems before the exam on the 20th"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
            />
            <div className="flex gap-3">
              <label className="flex-1 text-xs text-muted-foreground">
                Days
                <input
                  className="field mt-1 w-full"
                  type="number"
                  min={1}
                  max={60}
                  value={days}
                  onChange={(event) => setDays(Number(event.target.value))}
                />
              </label>
              <label className="flex-1 text-xs text-muted-foreground">
                Hours per day
                <input
                  className="field mt-1 w-full"
                  type="number"
                  min={0.5}
                  max={16}
                  step={0.5}
                  value={hours}
                  onChange={(event) => setHours(Number(event.target.value))}
                />
              </label>
            </div>
            <button className="btn-primary px-4 py-2 text-sm" disabled={busy}>
              {busy ? "Planning…" : "Plan and save sessions"}
            </button>
          </form>

          {error ? <p className="mt-4 text-sm text-red-500">{error}</p> : null}
          {plan ? (
            <p className="mt-4 text-sm text-muted-foreground">
              {plan.length} session(s) added. {note}
            </p>
          ) : null}
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Next 60 days</h2>
          {events.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing scheduled yet.</p>
          ) : (
            <ul className="space-y-2">
              {events.map((event) => (
                <li key={event.id} className="card flex items-start justify-between gap-4 p-4">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{event.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(event.starts_at)} · {event.category}
                      {event.source === "ai" ? " · planned by AI" : ""}
                    </p>
                    {event.description ? (
                      <p className="mt-1 text-sm text-muted-foreground">{event.description}</p>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    className="btn-ghost px-3 py-1.5 text-xs"
                    onClick={async () => {
                      if (!token) return;
                      await api.deleteEvent(token, event.id);
                      void load();
                    }}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </WorkspacePage>
  );
}

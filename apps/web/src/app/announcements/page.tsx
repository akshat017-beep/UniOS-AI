"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkspacePage } from "@/components/require-auth";
import { api, type Announcement, type UniNotification } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function CampusPage() {
  const { token, hasRole } = useAuth();
  const canPublish = hasRole("FACULTY", "ADMIN", "CLUB", "SUPER_ADMIN");
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [notifications, setNotifications] = useState<UniNotification[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [audience, setAudience] = useState("ALL");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [list, inbox] = await Promise.all([
        api.announcements(token),
        api.notifications(token),
      ]);
      setAnnouncements(list);
      setNotifications(inbox);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not load campus updates");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function publish(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !title.trim()) return;
    setError("");
    try {
      await api.createAnnouncement(token, { title, body, audience, notify: true });
      setTitle("");
      setBody("");
      void load();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not publish");
    }
  }

  return (
    <WorkspacePage
      title="Campus"
      description="Announcements from your university and everything the system has notified you about."
    >
      {error ? <p className="mb-6 text-sm text-red-500">{error}</p> : null}

      {canPublish ? (
        <form onSubmit={publish} className="card mb-10 space-y-3 p-5">
          <h2 className="text-lg font-semibold">Publish an announcement</h2>
          <input
            className="field w-full"
            placeholder="Title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <textarea
            className="field min-h-24 w-full"
            placeholder="What everyone needs to know"
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
          <select
            className="field w-full sm:w-56"
            value={audience}
            onChange={(event) => setAudience(event.target.value)}
          >
            <option value="ALL">Everyone</option>
            <option value="STUDENT">Students</option>
            <option value="FACULTY">Faculty</option>
            <option value="CLUB">Clubs</option>
          </select>
          <button className="btn-primary px-4 py-2 text-sm">Publish and notify</button>
        </form>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="mb-3 text-lg font-semibold">Announcements</h2>
          {announcements.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nothing published yet.</p>
          ) : (
            <ul className="space-y-3">
              {announcements.map((announcement) => (
                <li key={announcement.id} className="card p-4">
                  <p className="font-medium">{announcement.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(announcement.created_at).toLocaleString()} · {announcement.audience}
                  </p>
                  <p className="mt-2 whitespace-pre-wrap text-sm">{announcement.body}</p>
                  {canPublish ? (
                    <button
                      type="button"
                      className="btn-ghost mt-3 px-3 py-1.5 text-xs"
                      onClick={async () => {
                        if (!token) return;
                        await api.deleteAnnouncement(token, announcement.id).catch(() => undefined);
                        void load();
                      }}
                    >
                      Delete
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">Your notifications</h2>
          {notifications.length === 0 ? (
            <p className="text-sm text-muted-foreground">You are all caught up.</p>
          ) : (
            <ul className="space-y-2">
              {notifications.map((notification) => (
                <li
                  key={notification.id}
                  className={`card p-4 ${notification.is_read ? "opacity-60" : ""}`}
                >
                  <p className="font-medium">{notification.title}</p>
                  <p className="text-sm text-muted-foreground">{notification.body}</p>
                  {!notification.is_read ? (
                    <button
                      type="button"
                      className="btn-ghost mt-2 px-3 py-1.5 text-xs"
                      onClick={async () => {
                        if (!token) return;
                        await api.markNotificationRead(token, notification.id);
                        void load();
                      }}
                    >
                      Mark as read
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </WorkspacePage>
  );
}

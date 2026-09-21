"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { SiteHeader } from "@/components/site-header";
import { useAuth } from "@/lib/auth-context";
import {
  ACCESS_TOKEN_KEY,
  api,
  streamMessage,
  type AIStatus,
  type AgentInfo,
  type ChatMessage,
  type Citation,
  type Conversation,
  type RoutingInfo,
} from "@/lib/api";

type Pending = { content: string; routing: RoutingInfo | null };

export default function ChatPage() {
  const router = useRouter();
  const { user, loading } = useAuth();

  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [routing, setRouting] = useState<RoutingInfo | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [input, setInput] = useState("");
  const [agentOverride, setAgentOverride] = useState("");
  const [useDocuments, setUseDocuments] = useState(false);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    setToken(user ? localStorage.getItem(ACCESS_TOKEN_KEY) : null);
  }, [user]);

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!token) return;
    void api.agents().then(setAgents).catch(() => undefined);
    void api.aiStatus(token).then(setStatus).catch(() => undefined);
    void api.conversations(token).then(setConversations).catch(() => undefined);
  }, [token]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const openConversation = useCallback(
    async (id: string) => {
      if (!token) return;
      setActiveId(id);
      setRouting(null);
      const detail = await api.conversation(token, id);
      setMessages(detail.messages);
    },
    [token],
  );

  const startNew = () => {
    setActiveId(null);
    setMessages([]);
    setRouting(null);
    setError(null);
  };

  async function send(event: React.FormEvent) {
    event.preventDefault();
    if (!token || !input.trim() || pending) return;

    const text = input.trim();
    setInput("");
    setError(null);
    setMessages((current) => [
      ...current,
      {
        id: `local-${Date.now()}`,
        role: "user",
        content: text,
        agent: null,
        model: null,
        created_at: new Date().toISOString(),
      },
    ]);
    setPending({ content: "", routing: null });
    setCitations([]);

    let conversationId = activeId;

    await streamMessage(
      token,
      {
        message: text,
        conversation_id: activeId,
        agent: agentOverride || null,
        use_documents: useDocuments,
      },
      {
        onMeta: (meta) => {
          conversationId = meta.conversation_id;
          setActiveId(meta.conversation_id);
          setRouting(meta.routing);
          setCitations(meta.citations ?? []);
          setPending((p) => (p ? { ...p, routing: meta.routing } : p));
        },
        onToken: (piece) =>
          setPending((p) => (p ? { ...p, content: p.content + piece } : { content: piece, routing })),
        onError: (detail) => {
          setError(detail);
          setPending(null);
        },
        onDone: () => {
          setPending(null);
          if (conversationId) void openConversation(conversationId);
          void api.conversations(token).then(setConversations).catch(() => undefined);
        },
      },
    );
  }

  async function remove(id: string) {
    if (!token) return;
    await api.deleteConversation(token, id);
    setConversations((list) => list.filter((c) => c.id !== id));
    if (activeId === id) startNew();
  }

  if (loading || !user) {
    return (
      <div className="min-h-screen">
        <SiteHeader />
        <main className="mx-auto max-w-6xl px-5 py-16 text-sm text-muted-foreground">Loading…</main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <SiteHeader />

      <main className="mx-auto grid max-w-6xl gap-4 px-5 py-6 lg:grid-cols-[260px_1fr]">
        <aside className="card flex max-h-[70vh] flex-col p-4 lg:max-h-[78vh]">
          <button type="button" onClick={startNew} className="btn-primary w-full py-2 text-sm">
            New conversation
          </button>
          <div className="mt-4 flex-1 space-y-1 overflow-y-auto">
            {conversations.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Your conversations are saved to your account and appear here.
              </p>
            ) : (
              conversations.map((conversation) => (
                <div
                  key={conversation.id}
                  className={`group flex items-center gap-1 rounded-lg px-2 py-2 text-sm ${
                    activeId === conversation.id ? "bg-surface-muted" : ""
                  }`}
                >
                  <button
                    type="button"
                    onClick={() => void openConversation(conversation.id)}
                    className="flex-1 truncate text-left"
                  >
                    {conversation.title}
                  </button>
                  <button
                    type="button"
                    aria-label="Delete conversation"
                    onClick={() => void remove(conversation.id)}
                    className="text-xs text-muted-foreground opacity-0 transition group-hover:opacity-100"
                  >
                    ✕
                  </button>
                </div>
              ))
            )}
          </div>
        </aside>

        <section className="flex min-h-[70vh] flex-col">
          <div className="card flex flex-1 flex-col p-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b pb-3">
              <div>
                <h1 className="font-semibold">AI Assistant</h1>
                <p className="text-xs text-muted-foreground">
                  {routing
                    ? `Answered by the ${routing.title}${
                        routing.signals.length ? ` · matched: ${routing.signals.join(", ")}` : ""
                      }`
                    : "Your question is routed automatically to the right agent."}
                </p>
              </div>
              <label className="flex items-center gap-2 text-xs text-muted-foreground">
                <input
                  type="checkbox"
                  checked={useDocuments}
                  onChange={(event) => setUseDocuments(event.target.checked)}
                />
                Answer from my documents
              </label>
              <select
                value={agentOverride}
                onChange={(event) => setAgentOverride(event.target.value)}
                className="field w-auto py-1 text-xs"
                aria-label="Choose an agent"
              >
                <option value="">Automatic routing</option>
                {agents.map((agent) => (
                  <option key={agent.name} value={agent.name}>
                    {agent.title}
                  </option>
                ))}
              </select>
            </div>

            {status && !status.configured ? (
              <p className="mt-3 rounded-lg border border-dashed p-3 text-xs text-muted-foreground">
                No AI provider is configured yet, so answers are unavailable. Set{" "}
                <code>AI_BASE_URL</code>, <code>AI_MODEL</code> and <code>AI_API_KEY</code> in your
                environment — any OpenAI-compatible provider, or a local open-source server, works.
              </p>
            ) : null}

            <div className="mt-3 flex-1 space-y-3 overflow-y-auto pr-1">
              {messages.length === 0 && !pending ? (
                <p className="text-sm text-muted-foreground">
                  Ask anything about your studies, code, research, career or campus.
                </p>
              ) : null}

              {messages.map((message) => (
                <article
                  key={message.id}
                  className={`rounded-xl p-3 text-sm ${
                    message.role === "user" ? "bg-surface-muted" : "border"
                  }`}
                >
                  <p className="mb-1 text-xs text-muted-foreground">
                    {message.role === "user" ? "You" : `Assistant · ${message.agent ?? "agent"}`}
                  </p>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.citations && message.citations.length > 0 ? (
                    <ul className="mt-2 space-y-1 border-t pt-2 text-xs text-muted-foreground">
                      {message.citations.map((citation, index) => (
                        <li key={index}>
                          [{index + 1}] {citation.document_title} — page {citation.page}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              ))}

              {pending ? (
                <article className="rounded-xl border p-3 text-sm">
                  <p className="mb-1 text-xs text-muted-foreground">
                    {pending.routing ? `Assistant · ${pending.routing.title}` : "Thinking…"}
                  </p>
                  <p className="whitespace-pre-wrap">{pending.content || "…"}</p>
                  {citations.length > 0 ? (
                    <ul className="mt-2 space-y-1 border-t pt-2 text-xs text-muted-foreground">
                      {citations.map((citation, index) => (
                        <li key={index}>
                          [{index + 1}] {citation.document_title} — page {citation.page}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              ) : null}

              {error ? (
                <p className="rounded-xl border border-dashed p-3 text-sm text-muted-foreground">
                  {error}
                </p>
              ) : null}

              <div ref={bottomRef} />
            </div>

            <form onSubmit={send} className="mt-3 flex items-end gap-2 border-t pt-3">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) void send(event as never);
                }}
                rows={2}
                placeholder="Ask UniOS AI…"
                className="field flex-1 resize-none"
              />
              <button type="submit" disabled={!input.trim() || !!pending} className="btn-primary px-4 py-2 text-sm">
                Send
              </button>
            </form>
            <p className="mt-2 text-xs text-muted-foreground">
              AI-generated content. Verify anything university-specific with the responsible office.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}

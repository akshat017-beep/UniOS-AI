/** Thin typed client for the UniOS AI API. Only the public base URL reaches the browser. */

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const ACCESS_TOKEN_KEY = "unios.access_token";
export const REFRESH_TOKEN_KEY = "unios.refresh_token";

export type UserRole = "STUDENT" | "FACULTY" | "ADMIN" | "CLUB" | "SUPER_ADMIN";

export interface Profile {
  university: string | null;
  department: string | null;
  degree: string | null;
  branch: string | null;
  semester: number | null;
  enrollment_number: string | null;
  interests: string | null;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  profile: Profile | null;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new ApiError("Cannot reach the server. Check that the API is running.", 0);
  }

  if (response.status === 204) return undefined as T;

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body.detail === "string" ? body.detail : "Something went wrong";
    throw new ApiError(detail, response.status);
  }
  return body as T;
}

export interface AgentInfo {
  name: string;
  title: string;
  description: string;
}

export interface RoutingInfo {
  agent: string;
  title: string;
  confidence: number;
  signals: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent: string | null;
  model: string | null;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: ChatMessage[];
}

export interface AIStatus {
  configured: boolean;
  provider: string;
  model: string | null;
  detail: string;
}

export const api = {
  register: (input: { email: string; password: string; full_name: string; role?: UserRole }) =>
    request<TokenPair>("/auth/register", { method: "POST", body: JSON.stringify(input) }),

  login: (input: { email: string; password: string }) =>
    request<TokenPair>("/auth/login", { method: "POST", body: JSON.stringify(input) }),

  refresh: (refreshToken: string) =>
    request<TokenPair>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  logout: (token: string) => request<void>("/auth/logout", { method: "POST" }, token),

  me: (token: string) => request<User>("/auth/me", { method: "GET" }, token),

  agents: () => request<AgentInfo[]>("/agents", { method: "GET" }),

  aiStatus: (token: string) => request<AIStatus>("/agents/status", { method: "GET" }, token),

  conversations: (token: string) =>
    request<Conversation[]>("/chat/conversations", { method: "GET" }, token),

  conversation: (token: string, id: string) =>
    request<ConversationDetail>(`/chat/conversations/${id}`, { method: "GET" }, token),

  deleteConversation: (token: string, id: string) =>
    request<void>(`/chat/conversations/${id}`, { method: "DELETE" }, token),

  sendMessage: (
    token: string,
    input: { message: string; conversation_id?: string | null; agent?: string | null },
  ) =>
    request<{ conversation_id: string; routing: RoutingInfo; message: ChatMessage }>(
      "/chat/messages",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),
};

/**
 * Streamed reply over server-sent events. Falls back to an error callback when
 * the provider is not configured — nothing is ever invented client-side.
 */
export async function streamMessage(
  token: string,
  input: { message: string; conversation_id?: string | null; agent?: string | null },
  handlers: {
    onMeta?: (meta: { conversation_id: string; routing: RoutingInfo }) => void;
    onToken?: (text: string) => void;
    onError?: (detail: string) => void;
    onDone?: () => void;
  },
): Promise<void> {
  const response = await fetch(`${API_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(input),
  });

  if (!response.ok || !response.body) {
    const body = await response.json().catch(() => null);
    handlers.onError?.(
      (body && typeof body.detail === "string" && body.detail) || "The assistant is unavailable.",
    );
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const eventLine = frame.split("\n").find((l) => l.startsWith("event:"));
      const dataLine = frame.split("\n").find((l) => l.startsWith("data:"));
      if (!eventLine || !dataLine) continue;
      const event = eventLine.slice(6).trim();
      let data: Record<string, unknown>;
      try {
        data = JSON.parse(dataLine.slice(5).trim());
      } catch {
        continue;
      }
      if (event === "meta") handlers.onMeta?.(data as never);
      else if (event === "token") handlers.onToken?.(String(data.text ?? ""));
      else if (event === "error") handlers.onError?.(String(data.detail ?? "Provider error"));
      else if (event === "done") handlers.onDone?.();
    }
  }
}

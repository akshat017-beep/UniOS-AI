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

export interface Citation {
  document_id: string;
  document_title: string;
  page: number;
  snippet: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent: string | null;
  model: string | null;
  created_at: string;
  citations?: Citation[];
}

export interface UniDocument {
  id: string;
  title: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  pages: number;
  status: string;
  error: string | null;
  created_at: string;
}

export interface RagStatus {
  embeddings_configured: boolean;
  provider: string;
  model: string | null;
  vector_backend: string;
  detail: string;
}

export interface GenerationResult {
  content: string;
  model: string;
  agent: string;
  citations: Citation[];
  injection_warnings: string[];
}

export interface CodingStatus {
  execution_enabled: boolean;
  languages: { id: string; label: string; available: boolean }[];
  timeout_seconds: number;
  isolation_note: string;
}

export interface RunResult {
  stdout: string;
  stderr: string;
  exit_code: number;
  timed_out: boolean;
  language: string;
}

export interface UniNotification {
  id: string;
  title: string;
  body: string;
  category: string;
  link: string | null;
  is_read: boolean;
  created_at: string;
}

export interface CalendarEvent {
  id: string;
  title: string;
  description: string;
  category: string;
  starts_at: string;
  ends_at: string | null;
  source: string;
}

export interface PlannedItem {
  title: string;
  description: string;
  category: string;
  starts_at: string;
  ends_at: string | null;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  audience: string;
  is_published: boolean;
  created_at: string;
  author_id: string;
}

export interface SearchHit {
  kind: string;
  id: string;
  title: string;
  snippet: string;
  link: string;
}

export interface AdminStats {
  users_total: number;
  users_by_role: Record<string, number>;
  conversations_total: number;
  messages_total: number;
  documents_total: number;
  document_chunks_total: number;
  announcements_total: number;
  ai_configured: boolean;
  embeddings_configured: boolean;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface MultimodalStatus {
  vision_configured: boolean;
  vision_model: string | null;
  transcription_configured: boolean;
  transcription_model: string | null;
  detail: string;
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

  sendMessage: (token: string, input: SendMessageInput) =>
    request<{ conversation_id: string; routing: RoutingInfo; message: ChatMessage }>(
      "/chat/messages",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),

  // ----------------------------------------------------------------- documents
  ragStatus: (token: string) => request<RagStatus>("/documents/status", { method: "GET" }, token),

  documents: (token: string) => request<UniDocument[]>("/documents", { method: "GET" }, token),

  uploadDocument: async (token: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${API_URL}/api/v1/documents`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(
        (body && typeof body.detail === "string" && body.detail) || "Upload failed",
        response.status,
      );
    }
    return body as UniDocument;
  },

  deleteDocument: (token: string, id: string) =>
    request<void>(`/documents/${id}`, { method: "DELETE" }, token),

  searchDocuments: (token: string, input: { query: string; document_ids?: string[] }) =>
    request<{ citations: Citation[]; injection_warnings: string[] }>(
      "/documents/search",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),

  // --------------------------------------------------------------- workspaces
  studyMaterial: (
    token: string,
    input: { topic: string; format: string; level?: string; document_ids?: string[] },
  ) =>
    request<GenerationResult>(
      "/tools/study-material",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),

  research: (token: string, input: { topic: string; format: string; document_ids?: string[] }) =>
    request<GenerationResult>(
      "/tools/research",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),

  resume: (token: string, input: Record<string, string>) =>
    request<GenerationResult>("/tools/resume", { method: "POST", body: JSON.stringify(input) }, token),

  codingStatus: (token: string) =>
    request<CodingStatus>("/coding/status", { method: "GET" }, token),

  runCode: (token: string, input: { language: string; source: string; stdin?: string }) =>
    request<RunResult>("/coding/run", { method: "POST", body: JSON.stringify(input) }, token),

  multimodalStatus: (token: string) =>
    request<MultimodalStatus>("/multimodal/status", { method: "GET" }, token),

  transcribe: async (token: string, file: Blob, filename = "recording.webm") => {
    const form = new FormData();
    form.append("file", file, filename);
    const response = await fetch(`${API_URL}/api/v1/multimodal/transcribe`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(
        (body && typeof body.detail === "string" && body.detail) || "Transcription failed",
        response.status,
      );
    }
    return body as { text: string; model: string };
  },

  askAboutImage: async (token: string, file: File, question: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("question", question);
    const response = await fetch(`${API_URL}/api/v1/multimodal/image`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const body = await response.json().catch(() => null);
    if (!response.ok) {
      throw new ApiError(
        (body && typeof body.detail === "string" && body.detail) || "Image request failed",
        response.status,
      );
    }
    return body as { answer: string; model: string };
  },

  // ------------------------------------------------------------ campus platform
  notifications: (token: string) =>
    request<UniNotification[]>("/university/notifications", { method: "GET" }, token),

  markNotificationRead: (token: string, id: string) =>
    request<UniNotification>(`/university/notifications/${id}/read`, { method: "POST" }, token),

  events: (token: string, days = 30) =>
    request<CalendarEvent[]>(`/university/events?days=${days}`, { method: "GET" }, token),

  createEvent: (
    token: string,
    input: { title: string; description?: string; category?: string; starts_at: string; ends_at?: string | null },
  ) =>
    request<CalendarEvent>("/university/events", { method: "POST", body: JSON.stringify(input) }, token),

  deleteEvent: (token: string, id: string) =>
    request<void>(`/university/events/${id}`, { method: "DELETE" }, token),

  planSchedule: (
    token: string,
    input: { goal: string; days: number; hours_per_day: number; save: boolean },
  ) =>
    request<{ items: PlannedItem[]; saved: boolean; model: string; note: string }>(
      "/university/plan",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),

  announcements: (token: string) =>
    request<Announcement[]>("/university/announcements", { method: "GET" }, token),

  createAnnouncement: (
    token: string,
    input: { title: string; body: string; audience?: string; notify?: boolean },
  ) =>
    request<Announcement>(
      "/university/announcements",
      { method: "POST", body: JSON.stringify(input) },
      token,
    ),

  deleteAnnouncement: (token: string, id: string) =>
    request<void>(`/university/announcements/${id}`, { method: "DELETE" }, token),

  search: (token: string, query: string) =>
    request<{ query: string; hits: SearchHit[] }>(
      `/search?q=${encodeURIComponent(query)}`,
      { method: "GET" },
      token,
    ),

  // -------------------------------------------------------------------- admin
  adminStats: (token: string) => request<AdminStats>("/admin/stats", { method: "GET" }, token),

  adminUsers: (token: string, q = "") =>
    request<AdminUser[]>(`/admin/users${q ? `?q=${encodeURIComponent(q)}` : ""}`, { method: "GET" }, token),

  setUserActive: (token: string, id: string, isActive: boolean) =>
    request<AdminUser>(`/admin/users/${id}/active?is_active=${isActive}`, { method: "POST" }, token),

  adminMetrics: (token: string) =>
    request<Record<string, unknown>>("/admin/metrics", { method: "GET" }, token),
};

export interface SendMessageInput {
  message: string;
  conversation_id?: string | null;
  agent?: string | null;
  document_ids?: string[] | null;
  use_documents?: boolean;
}

/**
 * Streamed reply over server-sent events. Falls back to an error callback when
 * the provider is not configured — nothing is ever invented client-side.
 */
export async function streamMessage(
  token: string,
  input: SendMessageInput,
  handlers: {
    onMeta?: (meta: {
      conversation_id: string;
      routing: RoutingInfo;
      citations?: Citation[];
      injection_warnings?: string[];
    }) => void;
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

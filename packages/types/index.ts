/**
 * Shared contracts between the web app and the API.
 * Keep these in sync with the Pydantic schemas in apps/api/app/schemas.
 */

export type UserRole = "STUDENT" | "FACULTY" | "ADMIN" | "CLUB" | "SUPER_ADMIN";

export type AgentName =
  | "study"
  | "research"
  | "coding"
  | "career"
  | "document"
  | "campus"
  | "performance"
  | "communication"
  | "admin";

export interface Citation {
  document_id: string;
  document_title: string;
  page_number: number | null;
  snippet: string;
}

export interface AgentStep {
  label: string;
  status: "pending" | "running" | "done" | "failed";
}

// Cliente HTTP tipado del kiosco. Todas las rutas pasan por el proxy de Vite.

import type { Lang } from "./i18n";

export type LocalizedText = { es: string; "ca-valencia": string };

export type CatalogItem = {
  id: string;
  name: LocalizedText;
  description: LocalizedText | null;
  status: "available" | "coming_soon";
  execution_mode: "information" | "assisted" | "integrated" | "referral";
};

export type Procedure = CatalogItem & {
  official_sources: string[];
  requirements: LocalizedText[];
  required_fields: string[];
  confirmation_required: boolean;
};

export type SessionInfo = {
  session_id: string;
  language: Lang;
  expires_in_seconds: number;
  data_keys: string[];
};

export type IntentResult = {
  intent: string;
  confidence: number;
  procedure_id: string | null;
  next_action: "SHOW_PROCEDURE" | "ASK_CLARIFICATION" | "REFER_TO_HUMAN";
  clarification: string | null;
};

export type ExecutionResult = {
  status: "completed" | "failed" | "user_handoff";
  receipt: Record<string, string> | null;
  message: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok && response.status !== 204) {
    throw new Error(`HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  createSession: (language: Lang) =>
    request<SessionInfo>("/api/session", {
      method: "POST",
      body: JSON.stringify({ language }),
    }),
  extendSession: (sessionId: string) =>
    request<SessionInfo>(`/api/session/${sessionId}/extend`, { method: "POST" }),
  endSession: (sessionId: string) =>
    request<void>(`/api/session/${sessionId}`, { method: "DELETE" }),
  getCatalog: () => request<CatalogItem[]>("/api/catalog"),
  getProcedure: (id: string) => request<Procedure>(`/api/catalog/${id}`),
  classifyIntent: (text: string, language: Lang) =>
    request<IntentResult>("/api/assistant/intent", {
      method: "POST",
      body: JSON.stringify({ text, language }),
    }),
  executeProcedure: (procedureId: string, sessionId: string) =>
    request<ExecutionResult>(`/api/procedures/${procedureId}/execute`, {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, confirmed: true }),
    }),
  printReceipt: (lines: string[]) =>
    request<{ job_id: string }>("/device/printer/print", {
      method: "POST",
      body: JSON.stringify({ lines }),
    }),
};

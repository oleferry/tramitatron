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

export type DocumentClass = "dni" | "sip_card";

export type ExtractedField = {
  field: string;
  value: string;
  confidence: number;
  validator: string;
  status: "VALID" | "REVIEW_REQUIRED" | "INVALID";
};

export type DocumentExtraction = {
  document_id: string;
  document_class: DocumentClass;
  fields: ExtractedField[];
};

export type ConfirmDocumentResponse = {
  accepted: boolean;
  fields: ExtractedField[];
};

export type AskResponse = {
  found: boolean;
  answer: string | null;
  source: {
    organismo: string;
    title: string;
    url: string;
    fetched_at: string;
  } | null;
};

export type CameraCapture = {
  status: string;
  image_base64: string;
  mime_type: "image/png" | "image/jpeg";
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
  ask: (text: string, language: Lang, procedureId?: string) =>
    request<AskResponse>("/api/assistant/ask", {
      method: "POST",
      body: JSON.stringify({ text, language, procedure_id: procedureId ?? null }),
    }),
  captureCamera: () =>
    request<CameraCapture>("/device/camera/capture", { method: "POST" }),
  uploadDocument: (
    sessionId: string,
    documentClass: DocumentClass,
    imageBase64: string,
    mimeType: CameraCapture["mime_type"],
  ) =>
    request<DocumentExtraction>(`/api/session/${sessionId}/documents`, {
      method: "POST",
      body: JSON.stringify({
        document_class: documentClass,
        image_base64: imageBase64,
        mime_type: mimeType,
      }),
    }),
  confirmDocument: (sessionId: string, documentId: string, fields: Record<string, string>) =>
    request<ConfirmDocumentResponse>(
      `/api/session/${sessionId}/documents/${documentId}/confirm`,
      { method: "POST", body: JSON.stringify({ fields }) },
    ),
  printReceipt: (lines: string[]) =>
    request<{ job_id: string }>("/device/printer/print", {
      method: "POST",
      body: JSON.stringify({ lines }),
    }),
};

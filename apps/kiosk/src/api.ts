// Cliente HTTP tipado del kiosco. Todas las rutas pasan por el proxy de Vite.

import { demoActivated, demoApi } from "./demo";
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

// Explicación de cartas (TT-404). La respuesta separa a propósito los hechos
// leídos del documento de la lectura que hace el sistema.
export type LetterAnalysis = {
  letter_id: string;
  transcription_confidence: number;
  facts: {
    organismo: string | null;
    deadlines: string[];
    // Tipos de dato detectados ("dni", "iban"…), nunca los valores.
    sensitive_data: string[];
    excerpt: string;
  };
  explanation: {
    summary: string;
    risk_level: "normal" | "high";
    risk_terms: string[];
    ambiguous_deadline: boolean;
    recommend_human: boolean;
    human_advice: string | null;
    disclaimer: string;
  };
};

// Transcripción de voz. Ni el audio ni el texto se guardan en el servidor:
// el texto vive aquí, en memoria, hasta que la persona lo confirma o lo borra.
export type TranscriptResponse = {
  text: string;
  confidence: number;
  // En falso, la interfaz ofrece repetir en lugar de confirmar.
  usable: boolean;
};

export class NetworkError extends Error {}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    // Sin red: candidato a modo demostración.
    throw new NetworkError();
  }
  if (response.status === 204) return undefined as T;
  // Backend caído (5xx del proxy) o inexistente: en un despliegue estático
  // la ruta /api no existe y el servidor devuelve HTML en lugar de JSON.
  const contentType = response.headers.get("content-type") ?? "";
  if (response.status >= 500 || !contentType.includes("json")) {
    throw new NetworkError();
  }
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

const realApi = {
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
  explainLetter: (
    sessionId: string,
    imageBase64: string,
    mimeType: CameraCapture["mime_type"],
    language: Lang,
  ) =>
    request<LetterAnalysis>(`/api/session/${sessionId}/letters`, {
      method: "POST",
      body: JSON.stringify({
        image_base64: imageBase64,
        mime_type: mimeType,
        language,
      }),
    }),
  purgeLetter: (sessionId: string, letterId: string) =>
    request<void>(`/api/session/${sessionId}/letters/${letterId}`, { method: "DELETE" }),
  transcribeAudio: (
    sessionId: string,
    audioBase64: string,
    mimeType: string,
    language: Lang,
  ) =>
    request<TranscriptResponse>(`/api/session/${sessionId}/voice/transcribe`, {
      method: "POST",
      body: JSON.stringify({
        audio_base64: audioBase64,
        mime_type: mimeType,
        language,
      }),
    }),
  printReceipt: (lines: string[]) =>
    request<{ job_id: string }>("/device/printer/print", {
      method: "POST",
      body: JSON.stringify({ lines }),
    }),
};

// Métricas del panel (TT-602). Son señales agregadas y anónimas: un trámite
// iniciado o una valoración 1–5, nunca datos de la persona. Van "a fuego y
// olvido": si fallan (sin backend, preview estática) se ignoran en silencio y
// NO activan el modo demostración, porque no forman parte del flujo del usuario.
function fireAndForget(path: string, payload: unknown): void {
  void fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => undefined);
}

export const metrics = {
  procedureStarted: (procedureId: string) =>
    fireAndForget("/api/metrics/event", { type: "started", procedure_id: procedureId }),
  procedureAbandoned: (procedureId: string) =>
    fireAndForget("/api/metrics/event", { type: "abandoned", procedure_id: procedureId }),
  feedback: (rating: number) => fireAndForget("/api/metrics/feedback", { rating }),
};

// Latido del tótem (TT-601). Este kiosco ES un tótem del parque: reporta su
// versión y la salud de sus periféricos (leída del device-agent, si está) para
// que el panel institucional muestre el estado del dispositivo. Son datos del
// DISPOSITIVO, no de la persona. Va a fuego y olvido, como las métricas.
const TOTEM_ID = import.meta.env.VITE_TOTEM_ID || "totem-dev";
const APP_VERSION = import.meta.env.VITE_APP_VERSION || "dev";

type PeripheralState = "ok" | "down" | "unknown";
type Peripherals = {
  camera: PeripheralState;
  scanner: PeripheralState;
  printer: PeripheralState;
  paper_level: number;
};

async function readPeripherals(): Promise<Peripherals> {
  const unknown: Peripherals = {
    camera: "unknown",
    scanner: "unknown",
    printer: "unknown",
    paper_level: 100,
  };
  try {
    const res = await fetch("/device/health");
    if (!res.ok) return unknown;
    const h = await res.json();
    // El device-agent simulador informa "simulated"; se trata como operativo.
    const map = (v: unknown): PeripheralState =>
      v === "ok" || v === "simulated" ? "ok" : v ? "down" : "unknown";
    return {
      camera: map(h.camera),
      scanner: map(h.scanner),
      printer: map(h.printer),
      paper_level: typeof h.paper_level === "number" ? h.paper_level : 100,
    };
  } catch {
    return unknown;
  }
}

export const telemetry = {
  async heartbeat(): Promise<void> {
    const peripherals = await readPeripherals();
    fireAndForget(`/api/totems/${encodeURIComponent(TOTEM_ID)}/heartbeat`, {
      version: APP_VERSION,
      peripherals,
    });
  },
};

// Cada llamada intenta el backend real; si no hay red o no existe backend
// (preview estática), pasa al modo demostración y lo señala en la interfaz.
function withDemoFallback<A extends unknown[], R>(
  real: (...args: A) => Promise<R>,
  demo: (...args: A) => Promise<R>,
): (...args: A) => Promise<R> {
  return async (...args: A) => {
    try {
      return await real(...args);
    } catch (error) {
      if (error instanceof NetworkError) {
        demoActivated();
        return demo(...args);
      }
      throw error;
    }
  };
}

export const api: typeof realApi = {
  createSession: withDemoFallback(realApi.createSession, demoApi.createSession),
  extendSession: withDemoFallback(realApi.extendSession, demoApi.extendSession),
  endSession: withDemoFallback(realApi.endSession, demoApi.endSession),
  getCatalog: withDemoFallback(realApi.getCatalog, demoApi.getCatalog),
  getProcedure: withDemoFallback(realApi.getProcedure, demoApi.getProcedure),
  classifyIntent: withDemoFallback(realApi.classifyIntent, demoApi.classifyIntent),
  ask: withDemoFallback(realApi.ask, demoApi.ask),
  captureCamera: withDemoFallback(realApi.captureCamera, demoApi.captureCamera),
  uploadDocument: withDemoFallback(realApi.uploadDocument, demoApi.uploadDocument),
  confirmDocument: withDemoFallback(realApi.confirmDocument, demoApi.confirmDocument),
  executeProcedure: withDemoFallback(realApi.executeProcedure, demoApi.executeProcedure),
  explainLetter: withDemoFallback(realApi.explainLetter, demoApi.explainLetter),
  purgeLetter: withDemoFallback(realApi.purgeLetter, demoApi.purgeLetter),
  transcribeAudio: withDemoFallback(realApi.transcribeAudio, demoApi.transcribeAudio),
  printReceipt: withDemoFallback(realApi.printReceipt, demoApi.printReceipt),
};

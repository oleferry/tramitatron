// Modo demostración: implementación local de la API para despliegues sin
// backend (p. ej. la preview pública en Vercel). Se activa automáticamente
// cuando la red falla y se señala con un distintivo visible en la cabecera.
// Todos los datos son sintéticos; no hay ninguna llamada externa.

import type {
  AskResponse,
  CameraCapture,
  CatalogItem,
  ConfirmDocumentResponse,
  DocumentClass,
  DocumentExtraction,
  ExecutionResult,
  ExtractedField,
  IntentResult,
  Procedure,
  SessionInfo,
} from "./api";
import type { Lang } from "./i18n";

let active = false;

export function demoActivated(): void {
  if (!active) {
    active = true;
    window.dispatchEvent(new CustomEvent("tramitatron:demo"));
  }
}

export function isDemoActive(): boolean {
  return active;
}

const PROCEDURES: Procedure[] = [
  {
    id: "demo.mock.appointment",
    name: { es: "Trámite de demostración", "ca-valencia": "Tràmit de demostració" },
    description: {
      es: "Recorrido completo de ejemplo para probar el kiosco sin tocar ningún portal real.",
      "ca-valencia":
        "Recorregut complet d'exemple per a provar el quiosc sense tocar cap portal real.",
    },
    status: "available",
    execution_mode: "assisted",
    official_sources: [],
    requirements: [
      {
        es: "Es una demostración con un documento sintético. No se escanea tu DNI real.",
        "ca-valencia":
          "És una demostració amb un document sintètic. No s'escaneja el teu DNI real.",
      },
    ],
    required_fields: ["dni_number"],
    confirmation_required: true,
  },
  {
    id: "gva.health.primary-care.appointment",
    name: { es: "Cita de atención primaria", "ca-valencia": "Cita d'atenció primària" },
    description: {
      es: "Pedir cita con tu médico o enfermera del centro de salud (Conselleria de Sanidad).",
      "ca-valencia":
        "Demanar cita amb el teu metge o infermera del centre de salut (Conselleria de Sanitat).",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://www.san.gva.es/es/web/portal-del-paciente"],
    requirements: [
      { es: "Tarjeta SIP (o su número).", "ca-valencia": "Targeta SIP (o el seu número)." },
      { es: "Fecha de nacimiento.", "ca-valencia": "Data de naixement." },
    ],
    required_fields: ["sip_number", "birth_date"],
    confirmation_required: true,
  },
  {
    id: "sitval.itv.appointment",
    name: { es: "Cita previa ITV", "ca-valencia": "Cita prèvia ITV" },
    description: {
      es: "Reservar cita para la inspección técnica del vehículo en centros SITVAL de Castellón.",
      "ca-valencia":
        "Reservar cita per a la inspecció tècnica del vehicle en centres SITVAL de Castelló.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://sitval.com/"],
    requirements: [
      { es: "Matrícula del vehículo.", "ca-valencia": "Matrícula del vehicle." },
      {
        es: "Tipo de vehículo (coche, moto, furgoneta…).",
        "ca-valencia": "Tipus de vehicle (cotxe, moto, furgoneta…).",
      },
    ],
    required_fields: ["license_plate", "vehicle_type"],
    confirmation_required: true,
  },
];

const DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE";

function validDni(value: string): boolean {
  const match = /^(\d{8})([A-Za-z])$/.exec(value.trim());
  if (!match) return false;
  return DNI_LETTERS[parseInt(match[1], 10) % 23] === match[2].toUpperCase();
}

function validateField(field: string, value: string): ExtractedField["status"] {
  if (field === "dni_number") return validDni(value) ? "VALID" : "INVALID";
  if (field === "sip_number") return /^\d{8}$/.test(value.trim()) ? "VALID" : "INVALID";
  if (field === "birth_date")
    return /^\d{4}-\d{2}-\d{2}$/.test(value.trim()) ? "VALID" : "INVALID";
  return value.trim() ? "VALID" : "INVALID";
}

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "");
}

const ASK_ANSWERS: { pattern: RegExp; answer: string; source: AskResponse["source"] }[] = [
  {
    pattern: /\b(itv|vehicul|vehicle|coche|cotxe|moto|matricul)/,
    answer:
      "SITVAL es la página oficial para solicitar cita previa en todas las estaciones ITV de la Comunidad Valenciana. Reserva fácilmente tu cita en Alicante, Valencia y Castellón y asegúrate de cumplir con la inspección técnica de vehículos con total confianza.",
    source: {
      organismo: "SITVAL",
      title: "Cita previa ITV en la Comunitat Valenciana",
      url: "https://sitval.com/",
      fetched_at: "2026-07-17",
    },
  },
  {
    pattern: /\b(medic|metge|salud|salut|cita|sip|telefono|telefon)/,
    answer:
      "Cita previa — Sede electrónica de la Generalitat Valenciana.\nAtención telefónica 012.\nOficinas de atención presencial PROP.\nOficinas de registro.\nOficina Virtual de Atención a la Ciudadanía.",
    source: {
      organismo: "Generalitat Valenciana",
      title: "Cita previa de la Generalitat",
      url: "https://sede.gva.es/es/cita-previa",
      fetched_at: "2026-07-17",
    },
  },
];

export const demoApi = {
  createSession: async (language: Lang): Promise<SessionInfo> => ({
    session_id: `demo-${Math.random().toString(36).slice(2, 10)}`,
    language,
    expires_in_seconds: 1200,
    data_keys: [],
  }),

  extendSession: async (sessionId: string): Promise<SessionInfo> => ({
    session_id: sessionId,
    language: "es",
    expires_in_seconds: 1200,
    data_keys: [],
  }),

  endSession: async (): Promise<void> => undefined,

  getCatalog: async (): Promise<CatalogItem[]> =>
    PROCEDURES.map(({ id, name, description, status, execution_mode }) => ({
      id,
      name,
      description,
      status,
      execution_mode,
    })),

  getProcedure: async (id: string): Promise<Procedure> => {
    const found = PROCEDURES.find((p) => p.id === id);
    if (!found) throw new Error("HTTP 404");
    return found;
  },

  classifyIntent: async (text: string, language: Lang): Promise<IntentResult> => {
    const normalized = normalize(text);
    const rules: [RegExp, string, string][] = [
      [/\b(medic|metge|salud|salut|doctor)/, "BOOK_HEALTH_APPOINTMENT", "gva.health.primary-care.appointment"],
      [/\b(itv|vehicul|vehicle|coche|cotxe|moto)/, "BOOK_ITV_APPOINTMENT", "sitval.itv.appointment"],
      [/\b(demo|demostraci|prueba|prova)/, "DEMO_PROCEDURE", "demo.mock.appointment"],
    ];
    for (const [pattern, intent, procedureId] of rules) {
      if (pattern.test(normalized)) {
        return {
          intent,
          confidence: 0.92,
          procedure_id: procedureId,
          next_action: "SHOW_PROCEDURE",
          clarification: null,
        };
      }
    }
    return {
      intent: "UNKNOWN",
      confidence: 0.2,
      procedure_id: null,
      next_action: "ASK_CLARIFICATION",
      clarification:
        language === "es"
          ? "No he entendido qué trámite necesitas. ¿Puedes decirlo con otras palabras?"
          : "No he entés quin tràmit necessites. Pots dir-ho amb altres paraules?",
    };
  },

  ask: async (text: string): Promise<AskResponse> => {
    const normalized = normalize(text);
    for (const entry of ASK_ANSWERS) {
      if (entry.pattern.test(normalized)) {
        return { found: true, answer: entry.answer, source: entry.source };
      }
    }
    return { found: false, answer: null, source: null };
  },

  captureCamera: async (): Promise<CameraCapture> => ({
    status: "simulated",
    image_base64: "ZGVtbw==",
    mime_type: "image/png",
  }),

  uploadDocument: async (
    _sessionId: string,
    documentClass: DocumentClass,
  ): Promise<DocumentExtraction> => ({
    document_id: `demo-doc-${Math.random().toString(36).slice(2, 8)}`,
    document_class: documentClass,
    fields:
      documentClass === "dni"
        ? [
            { field: "dni_number", value: "12345678Z", confidence: 0.97, validator: "dni_or_nie_v1", status: "VALID" },
            { field: "full_name", value: "PERSONA SINTÉTICA DEMO", confidence: 0.95, validator: "nonempty_v1", status: "VALID" },
            { field: "birth_date", value: "1957-03-14", confidence: 0.62, validator: "iso_date_v1", status: "REVIEW_REQUIRED" },
          ]
        : [
            { field: "sip_number", value: "01234567", confidence: 0.93, validator: "sip_format_v1", status: "VALID" },
            { field: "full_name", value: "PERSONA SINTÉTICA DEMO", confidence: 0.9, validator: "nonempty_v1", status: "VALID" },
          ],
  }),

  confirmDocument: async (
    _sessionId: string,
    _documentId: string,
    fields: Record<string, string>,
  ): Promise<ConfirmDocumentResponse> => {
    const results: ExtractedField[] = Object.entries(fields).map(([field, value]) => ({
      field,
      value,
      confidence: 1.0,
      validator: "demo",
      status: validateField(field, value),
    }));
    return { accepted: results.every((f) => f.status === "VALID"), fields: results };
  },

  executeProcedure: async (procedureId: string): Promise<ExecutionResult> => {
    if (procedureId !== "demo.mock.appointment") throw new Error("HTTP 409");
    return {
      status: "completed",
      receipt: {
        reference: `DEMO-${Math.random().toString(16).slice(2, 10).toUpperCase()}`,
        timestamp: new Date().toISOString(),
        kind: "demo",
      },
      message: null,
    };
  },

  printReceipt: async (): Promise<{ job_id: string }> => ({ job_id: "demo-print" }),
};

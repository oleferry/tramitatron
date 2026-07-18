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
  {
    id: "mir.dni.renewal-appointment",
    name: {
      es: "Cita previa para renovar el DNI",
      "ca-valencia": "Cita prèvia per a renovar el DNI",
    },
    description: {
      es: "Reservar cita en una oficina de expedición para renovar tu Documento Nacional de Identidad.",
      "ca-valencia":
        "Reservar cita en una oficina d'expedició per a renovar el teu Document Nacional d'Identitat.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: [
      "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/cita-previa/",
      "https://www.citapreviadnie.es/",
    ],
    requirements: [
      { es: "Número de tu DNI o NIE.", "ca-valencia": "Número del teu DNI o NIE." },
      { es: "Fecha de nacimiento.", "ca-valencia": "Data de naixement." },
      {
        es: "Tu DNI actual, aunque esté caducado.",
        "ca-valencia": "El teu DNI actual, encara que estiga caducat.",
      },
    ],
    required_fields: ["dni_number", "birth_date"],
    confirmation_required: true,
  },
  {
    id: "aeat.cita-previa",
    name: { es: "Cita previa con Hacienda", "ca-valencia": "Cita prèvia amb Hisenda" },
    description: {
      es: "Reservar cita en una oficina de la Agencia Tributaria para Renta, requerimientos u otras gestiones.",
      "ca-valencia":
        "Reservar cita en una oficina de l'Agència Tributària per a Renda, requeriments o altres gestions.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: [
      "https://sede.agenciatributaria.gob.es/Sede/ayuda/consultas-informaticas/otros-servicios-ayuda-tecnica/peticion-cita-previa-traves-internet.html",
    ],
    requirements: [
      { es: "Número de DNI o NIE.", "ca-valencia": "Número de DNI o NIE." },
      {
        es: "Nombre y apellidos tal como aparecen en el documento.",
        "ca-valencia": "Nom i cognoms tal com apareixen al document.",
      },
    ],
    required_fields: ["dni_number", "full_name"],
    confirmation_required: true,
  },
  {
    id: "seg-social.inss.cita-previa",
    name: {
      es: "Cita previa con la Seguridad Social (pensiones y prestaciones)",
      "ca-valencia": "Cita prèvia amb la Seguretat Social (pensions i prestacions)",
    },
    description: {
      es: "Reservar cita en un centro de atención (CAISS) para pensiones, incapacidad, viudedad u otras prestaciones.",
      "ca-valencia":
        "Reservar cita en un centre d'atenció (CAISS) per a pensions, incapacitat, viudetat o altres prestacions.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: [
      "https://sede.seg-social.gob.es/wps/portal/sede/sede/Ciudadanos/cita+previa+para+pensiones+y+otras+prestaciones/202910SinC",
    ],
    requirements: [
      { es: "Número de DNI o NIE.", "ca-valencia": "Número de DNI o NIE." },
      {
        es: "Código postal para elegir la oficina más cercana.",
        "ca-valencia": "Codi postal per a triar l'oficina més pròxima.",
      },
    ],
    required_fields: ["dni_number", "postal_code"],
    confirmation_required: true,
  },
  {
    id: "seg-social.tgss.vida-laboral",
    name: { es: "Informe de vida laboral", "ca-valencia": "Informe de vida laboral" },
    description: {
      es: "Pedir el informe de vida laboral por SMS o para recibirlo por correo postal en casa (portal Import@ss).",
      "ca-valencia":
        "Demanar l'informe de vida laboral per SMS o per a rebre'l per correu postal a casa (portal Import@ss).",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: [
      "https://portal.seg-social.gob.es/wps/portal/importass/importass/Categorias/Vida+laboral+e+informes/Informes+sobre+tu+situacion+laboral/Informe+de+tu+vida+laboral",
    ],
    requirements: [
      {
        es: "Número de DNI o NIE y fecha de nacimiento.",
        "ca-valencia": "Número de DNI o NIE i data de naixement.",
      },
      {
        es: "Móvil comunicado previamente a la Seguridad Social (para el código SMS).",
        "ca-valencia": "Mòbil comunicat prèviament a la Seguretat Social (per al codi SMS).",
      },
    ],
    required_fields: ["dni_number", "birth_date", "phone_number"],
    confirmation_required: true,
  },
  {
    id: "gva.health.sip-renewal",
    name: {
      es: "Renovar o duplicar la tarjeta sanitaria SIP",
      "ca-valencia": "Renovar o duplicar la targeta sanitària SIP",
    },
    description: {
      es: "Pedir una tarjeta SIP nueva por pérdida o deterioro, con recogida en tu centro de salud.",
      "ca-valencia":
        "Demanar una targeta SIP nova per pèrdua o deteriorament, amb recollida al teu centre de salut.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://www.san.gva.es/es/web/tarjeta-sanitaria/tramites-tarjeta-sip"],
    requirements: [
      {
        es: "Número SIP, o bien DNI y fecha de nacimiento.",
        "ca-valencia": "Número SIP, o bé DNI i data de naixement.",
      },
      {
        es: "Si la tarjeta se ha perdido, hay que pagar una tasa (3,15 €).",
        "ca-valencia": "Si la targeta s'ha perdut, cal pagar una taxa (3,15 €).",
      },
    ],
    required_fields: ["sip_number", "birth_date"],
    confirmation_required: true,
  },
  {
    id: "sepe.cita-previa",
    name: {
      es: "Cita previa con el SEPE (paro y prestaciones)",
      "ca-valencia": "Cita prèvia amb el SEPE (atur i prestacions)",
    },
    description: {
      es: "Reservar cita en una oficina de prestaciones del SEPE para gestionar el paro u otras ayudas.",
      "ca-valencia":
        "Reservar cita en una oficina de prestacions del SEPE per a gestionar l'atur o altres ajudes.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: [
      "https://sede.sepe.gob.es/portalSede/procedimientos-y-servicios/personas/proteccion-por-desempleo/cita-previa",
    ],
    requirements: [
      { es: "Código postal de tu domicilio.", "ca-valencia": "Codi postal del teu domicili." },
      { es: "Número de DNI o NIE.", "ca-valencia": "Número de DNI o NIE." },
    ],
    required_fields: ["postal_code", "dni_number"],
    confirmation_required: true,
  },
  {
    id: "dgt.cita-previa",
    name: {
      es: "Cita previa con Tráfico (DGT)",
      "ca-valencia": "Cita prèvia amb Trànsit (DGT)",
    },
    description: {
      es: "Reservar cita en la Jefatura de Tráfico para renovar el carné de conducir, duplicados o canjes.",
      "ca-valencia":
        "Reservar cita en la Prefectura de Trànsit per a renovar el carnet de conduir, duplicats o bescanvis.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://sede.dgt.gob.es/es/otros-tramites/cita-previa/"],
    requirements: [
      { es: "Número de DNI o NIE.", "ca-valencia": "Número de DNI o NIE." },
      {
        es: "Saber qué gestión necesitas (renovación, duplicado, canje…).",
        "ca-valencia": "Saber quina gestió necessites (renovació, duplicat, bescanvi…).",
      },
    ],
    required_fields: ["dni_number", "procedure_type"],
    confirmation_required: true,
  },
  {
    id: "mir.extranjeria.cita-previa",
    name: {
      es: "Cita previa de extranjería (TIE, NIE, huellas)",
      "ca-valencia": "Cita prèvia d'estrangeria (TIE, NIE, empremtes)",
    },
    description: {
      es: "Reservar cita en la Oficina de Extranjería para la tarjeta TIE, el NIE o la toma de huellas.",
      "ca-valencia":
        "Reservar cita a l'Oficina d'Estrangeria per a la targeta TIE, el NIE o la presa d'empremtes.",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://icp.administracionelectronica.gob.es/icpplus/index.html"],
    requirements: [
      { es: "NIE o pasaporte en vigor.", "ca-valencia": "NIE o passaport en vigor." },
      {
        es: "Saber qué trámite necesitas (TIE, huellas, certificado…).",
        "ca-valencia": "Saber quin tràmit necessites (TIE, empremtes, certificat…).",
      },
    ],
    required_fields: ["nie_or_passport", "full_name"],
    confirmation_required: true,
  },
  {
    id: "castello.padron.certificado",
    name: {
      es: "Certificado o volante de empadronamiento (Castelló)",
      "ca-valencia": "Certificat o volant d'empadronament (Castelló)",
    },
    description: {
      es: "Cómo obtener el certificado o volante de empadronamiento del Ayuntamiento de Castelló de la Plana.",
      "ca-valencia":
        "Com obtindre el certificat o volant d'empadronament de l'Ajuntament de Castelló de la Plana.",
    },
    status: "available",
    execution_mode: "information",
    official_sources: [
      "https://www.castello.es/es/w/padron-habitantes",
      "https://www.castello.es/es/solicitud-cita-previa",
    ],
    requirements: [
      {
        es: "En la sede electrónica necesitarás identificarte con Cl@ve o certificado digital.",
        "ca-valencia":
          "En la seu electrònica necessitaràs identificar-te amb Cl@ve o certificat digital.",
      },
      {
        es: "También puedes pedir cita previa y recogerlo presencialmente en el Ayuntamiento.",
        "ca-valencia":
          "També pots demanar cita prèvia i arreplegar-lo presencialment a l'Ajuntament.",
      },
    ],
    required_fields: [],
    confirmation_required: true,
  },
  {
    id: "mjusticia.certificado-nacimiento",
    name: { es: "Certificado de nacimiento", "ca-valencia": "Certificat de naixement" },
    description: {
      es: "Cómo pedir un certificado de nacimiento del Registro Civil, online o presencialmente.",
      "ca-valencia":
        "Com demanar un certificat de naixement del Registre Civil, en línia o presencialment.",
    },
    status: "available",
    execution_mode: "information",
    official_sources: ["https://sede.mjusticia.gob.es/es/tramites"],
    requirements: [
      {
        es: "Para pedirlo online necesitarás identificarte con Cl@ve o certificado digital.",
        "ca-valencia":
          "Per a demanar-lo en línia necessitaràs identificar-te amb Cl@ve o certificat digital.",
      },
      {
        es: "También puede pedirse presencialmente en el Registro Civil.",
        "ca-valencia": "També pot demanar-se presencialment al Registre Civil.",
      },
    ],
    required_fields: [],
    confirmation_required: true,
  },
  {
    id: "mjusticia.antecedentes-penales",
    name: {
      es: "Certificado de antecedentes penales",
      "ca-valencia": "Certificat d'antecedents penals",
    },
    description: {
      es: "Cómo pedir el certificado de antecedentes penales del Ministerio de Justicia.",
      "ca-valencia":
        "Com demanar el certificat d'antecedents penals del Ministeri de Justícia.",
    },
    status: "available",
    execution_mode: "information",
    official_sources: ["https://sede.mjusticia.gob.es/es/tramites/certificado-antecedentes"],
    requirements: [
      {
        es: "Para pedirlo online necesitarás identificarte con Cl@ve o certificado digital.",
        "ca-valencia":
          "Per a demanar-lo en línia necessitaràs identificar-te amb Cl@ve o certificat digital.",
      },
      {
        es: "Suele emitirse en el momento o en un plazo de 24 horas.",
        "ca-valencia": "Sol emetre's en el moment o en un termini de 24 hores.",
      },
    ],
    required_fields: [],
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
    pattern: /\b(dni|documento nacional|pasaporte|passaport)\b/,
    answer:
      "Para renovar el DNI o el pasaporte es imprescindible reservar cita previa en una oficina de expedición. Puedes hacerlo en www.citapreviadnie.es con los datos de tu DNI o NIE. Lleva tu documento actual aunque esté caducado, una foto reciente y el justificante de la cita.",
    source: {
      organismo: "Ministerio del Interior",
      title: "Cita previa para el DNI",
      url: "https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/cita-previa/",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(hacienda|hisenda|renta|renda|irpf|declaracion|declaracio|impuesto|impost|tributari)/,
    answer:
      "La Agencia Tributaria atiende en sus oficinas con cita previa. Puedes pedirla por internet en la sede electrónica (sede.agenciatributaria.gob.es) sin necesidad de identificación electrónica, o por teléfono en el 91 333 5 333, eligiendo la oficina por provincia o código postal.",
    source: {
      organismo: "Agencia Tributaria",
      title: "Petición de cita previa por internet",
      url: "https://sede.agenciatributaria.gob.es/Sede/ayuda/consultas-informaticas/otros-servicios-ayuda-tecnica/peticion-cita-previa-traves-internet.html",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(vida laboral|cotizacion|cotitzacio)/,
    answer:
      "Puedes obtener el informe de tu vida laboral en el portal Import@ss de la Seguridad Social. Sin certificado digital puedes identificarte por SMS si tu móvil está comunicado a la Tesorería; si no, puedes pedir que te lo envíen por correo postal a tu domicilio.",
    source: {
      organismo: "Tesorería General de la Seguridad Social",
      title: "Informe de tu vida laboral (Import@ss)",
      url: "https://portal.seg-social.gob.es/wps/portal/importass/importass/Categorias/Vida+laboral+e+informes/Informes+sobre+tu+situacion+laboral/Informe+de+tu+vida+laboral",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(paro|atur|desempleo|desocupacio|sepe|subsidio|subsidi)\b/,
    answer:
      "El SEPE atiende en sus oficinas de prestaciones con cita previa. Puedes pedirla en la sede electrónica (sede.sepe.gob.es) indicando tu código postal para elegir oficina, o por teléfono. Muchas gestiones del paro también pueden hacerse por internet sin desplazarte.",
    source: {
      organismo: "Servicio Público de Empleo Estatal",
      title: "Cita previa del SEPE",
      url: "https://sede.sepe.gob.es/portalSede/procedimientos-y-servicios/personas/proteccion-por-desempleo/cita-previa",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(pension|pensio|jubilacion|jubilacio|viudedad|viudetat|incapacidad|incapacitat|seguridad social|seguretat social)/,
    answer:
      "Para pensiones y otras prestaciones, la Seguridad Social atiende en los centros CAISS con cita previa. Puedes pedirla por internet en la sede electrónica (sede.seg-social.gob.es) sin certificado digital, o por teléfono en el 901 10 65 70 / 91 541 25 30.",
    source: {
      organismo: "Instituto Nacional de la Seguridad Social",
      title: "Cita previa para pensiones y otras prestaciones",
      url: "https://sede.seg-social.gob.es/wps/portal/sede/sede/Ciudadanos/cita+previa+para+pensiones+y+otras+prestaciones/202910SinC",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(tarjeta sanitaria|targeta sanitaria|sip)\b/,
    answer:
      "Si tu tarjeta SIP se ha perdido o deteriorado, puedes pedir una nueva por internet con recogida en tu centro de salud. Solo necesitas el número SIP, o el DNI y la fecha de nacimiento. En caso de pérdida hay una tasa de 3,15 € (modelo 046-9679).",
    source: {
      organismo: "Conselleria de Sanidad (GVA)",
      title: "Trámites de la tarjeta SIP",
      url: "https://www.san.gva.es/es/web/tarjeta-sanitaria/tramites-tarjeta-sip",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(carne\w? de conducir|carnet de conduir|permiso de conducir|permis de conduir|trafico|transit|dgt|canje|bescanvi)/,
    answer:
      "Para trámites en la Jefatura de Tráfico (renovación del permiso, duplicados, canjes) pide cita previa en sede.dgt.gob.es: elige provincia y oficina, el tipo de trámite, y una fecha y hora disponibles. Los canjes de permiso extranjero siempre requieren cita.",
    source: {
      organismo: "Dirección General de Tráfico",
      title: "Cita previa en Jefaturas de Tráfico",
      url: "https://sede.dgt.gob.es/es/otros-tramites/cita-previa/",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(extranjeria|estrangeria|nie|tie|huellas|empremtes|residencia)\b/,
    answer:
      "Las citas de extranjería (tarjeta TIE, NIE, toma de huellas) se piden en el portal de las Administraciones Públicas: icp.administracionelectronica.gob.es. Elige tu provincia y el trámite; necesitarás tu NIE o pasaporte en vigor.",
    source: {
      organismo: "Secretaría de Estado de Administraciones Públicas",
      title: "Cita previa de extranjería",
      url: "https://sede.administracionespublicas.gob.es/pagina/index/directorio/icpplus",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(empadronamiento|empadronament|padron|padro\b|volante|volant)/,
    answer:
      "El Ayuntamiento de Castelló expide certificados y volantes de empadronamiento por su sede electrónica (con Cl@ve o certificado digital, el volante llega al momento) o presencialmente con cita previa en la Plaza Mayor, 1 (teléfono 964 226 010).",
    source: {
      organismo: "Ayuntamiento de Castelló de la Plana",
      title: "Padrón de habitantes",
      url: "https://www.castello.es/es/w/padron-habitantes",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(antecedentes|antecedents|penales|penals|nacimiento|naixement|registro civil|registre civil)/,
    answer:
      "Los certificados del Ministerio de Justicia (antecedentes penales, nacimiento, matrimonio…) se piden en sede.mjusticia.gob.es, identificándote con Cl@ve o certificado digital. El de antecedentes penales suele emitirse en el momento o en 24 horas. También pueden pedirse presencialmente.",
    source: {
      organismo: "Ministerio de Justicia",
      title: "Trámites de la Sede Electrónica",
      url: "https://sede.mjusticia.gob.es/es/tramites",
      fetched_at: "2026-07-18",
    },
  },
  {
    pattern: /\b(medic|metge|salud|salut|cita|telefono|telefon)/,
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
    // Espejo de las reglas del gateway (app/gateway/mock.py): las más
    // específicas primero, porque gana la primera coincidencia.
    const rules: [RegExp, string, string][] = [
      [/\b(vida laboral|informe laboral|cotizacion|cotitzacio)/, "REQUEST_WORK_HISTORY", "seg-social.tgss.vida-laboral"],
      [/\b(antecedentes|antecedents|penales|penals)/, "REQUEST_CRIMINAL_RECORD", "mjusticia.antecedentes-penales"],
      [/\b(nacimiento|naixement|registro civil|registre civil)/, "REQUEST_BIRTH_CERTIFICATE", "mjusticia.certificado-nacimiento"],
      [/\b(empadronamiento|empadronament|padron|padro\b|volante|volant)/, "REQUEST_CENSUS_CERTIFICATE", "castello.padron.certificado"],
      [/\b(tarjeta sanitaria|targeta sanitaria|sip)\b/, "RENEW_HEALTH_CARD", "gva.health.sip-renewal"],
      [/\b(medic|metge|salud|salut|doctor|ambulatori|centro de salud)/, "BOOK_HEALTH_APPOINTMENT", "gva.health.primary-care.appointment"],
      [/\b(itv|inspeccion tecnica|inspeccio tecnica)/, "BOOK_ITV_APPOINTMENT", "sitval.itv.appointment"],
      [/\b(carne\w? de conducir|carnet de conduir|permiso de conducir|permis de conduir|trafico|transit|dgt|canje|bescanvi)/, "BOOK_DGT_APPOINTMENT", "dgt.cita-previa"],
      [/\b(coche|cotxe|moto|vehicul|vehicle)/, "BOOK_ITV_APPOINTMENT", "sitval.itv.appointment"],
      [/\b(extranjeria|estrangeria|nie|tie|huellas|empremtes|residencia)\b/, "BOOK_IMMIGRATION_APPOINTMENT", "mir.extranjeria.cita-previa"],
      [/\b(dni|documento nacional|pasaporte|passaport)\b/, "BOOK_DNI_APPOINTMENT", "mir.dni.renewal-appointment"],
      [/\b(hacienda|hisenda|renta|renda|irpf|declaracion|declaracio|impuesto|impost|tributari)/, "BOOK_TAX_APPOINTMENT", "aeat.cita-previa"],
      [/\b(paro|atur|desempleo|desocupacio|sepe|subsidio|subsidi)\b/, "BOOK_SEPE_APPOINTMENT", "sepe.cita-previa"],
      [/\b(pension|pensio|jubilacion|jubilacio|viudedad|viudetat|incapacidad|incapacitat|seguridad social|seguretat social)/, "BOOK_INSS_APPOINTMENT", "seg-social.inss.cita-previa"],
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

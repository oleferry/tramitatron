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
  LetterAnalysis,
  Procedure,
  SessionInfo,
  TranscriptResponse,
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
    id: "demo.worker.appointment",
    name: {
      es: "Demostración de navegación asistida",
      "ca-valencia": "Demostració de navegació assistida",
    },
    description: {
      es: "Ejemplo del asistente que prepara una cita en un portal y te cede el paso final.",
      "ca-valencia":
        "Exemple de l'assistent que prepara una cita en un portal i et cedix el pas final.",
    },
    status: "available",
    execution_mode: "integrated",
    official_sources: [],
    requirements: [
      {
        es: "El sistema navega el portal de pruebas y precompleta lo que puede.",
        "ca-valencia": "El sistema navega el portal de proves i precompleta el que pot.",
      },
      {
        es: "El CAPTCHA y la confirmación de la cita los haces tú.",
        "ca-valencia": "El CAPTCHA i la confirmació de la cita els fas tu.",
      },
    ],
    required_fields: [],
    confirmation_required: true,
  },
  {
    id: "sacyl.health.primary-care",
    name: { es: "Cita de atención primaria", "ca-valencia": "Cita d'atenció primària" },
    description: {
      es: "Pedir cita con tu médico o enfermera del centro de salud (Sacyl, Castilla y León).",
      "ca-valencia":
        "Demanar cita amb el teu metge o infermera del centre de salut (Sacyl, Castella i Lleó).",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://www.saludcastillayleon.es/es/citaprevia"],
    requirements: [
      {
        es: "Número de tu tarjeta sanitaria de Castilla y León.",
        "ca-valencia": "Número de la teua targeta sanitària de Castella i Lleó.",
      },
      { es: "Fecha de nacimiento.", "ca-valencia": "Data de naixement." },
    ],
    required_fields: ["health_card_number", "birth_date"],
    confirmation_required: true,
  },
  {
    id: "jcyl.itv.info",
    name: { es: "Cita para la ITV", "ca-valencia": "Cita per a la ITV" },
    description: {
      es: "Cómo reservar cita para la inspección técnica del vehículo en Castilla y León.",
      "ca-valencia":
        "Com reservar cita per a la inspecció tècnica del vehicle a Castella i Lleó.",
    },
    status: "available",
    execution_mode: "information",
    official_sources: [
      "https://economia.jcyl.es/web/es/industria/inspeccion-tecnica-vehiculos.html",
    ],
    requirements: [
      {
        es: "En Castilla y León la ITV la gestionan estaciones concesionarias (ITEVELESA, TÜV SÜD…).",
        "ca-valencia":
          "A Castella i Lleó la ITV la gestionen estacions concessionàries (ITEVELESA, TÜV SÜD…).",
      },
      {
        es: "La cita se pide en la web de tu estación; ten a mano la matrícula y el permiso de circulación.",
        "ca-valencia":
          "La cita es demana en la web de la teua estació; tin a mà la matrícula i el permís de circulació.",
      },
    ],
    required_fields: [],
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
    id: "sacyl.health.card",
    name: {
      es: "Renovar o duplicar la tarjeta sanitaria",
      "ca-valencia": "Renovar o duplicar la targeta sanitària",
    },
    description: {
      es: "Pedir una tarjeta sanitaria nueva por pérdida o deterioro (Sacyl, Castilla y León).",
      "ca-valencia":
        "Demanar una targeta sanitària nova per pèrdua o deteriorament (Sacyl, Castella i Lleó).",
    },
    status: "coming_soon",
    execution_mode: "assisted",
    official_sources: ["https://www.saludcastillayleon.es/es/serviciosonline/tarjeta-sanitaria"],
    requirements: [
      {
        es: "Número de tarjeta sanitaria, o bien DNI y fecha de nacimiento.",
        "ca-valencia": "Número de targeta sanitària, o bé DNI i data de naixement.",
      },
      {
        es: "Si la tarjeta se ha perdido o roto, se solicita una nueva por internet.",
        "ca-valencia": "Si la targeta s'ha perdut o trencat, se'n sol·licita una de nova per internet.",
      },
    ],
    required_fields: ["health_card_number", "birth_date"],
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
    id: "padron.certificado",
    name: {
      es: "Certificado o volante de empadronamiento",
      "ca-valencia": "Certificat o volant d'empadronament",
    },
    description: {
      es: "Cómo obtener el certificado o volante de empadronamiento en tu ayuntamiento.",
      "ca-valencia": "Com obtindre el certificat o volant d'empadronament al teu ajuntament.",
    },
    status: "available",
    execution_mode: "information",
    official_sources: [],
    requirements: [
      {
        es: "El empadronamiento lo gestiona tu ayuntamiento, en su sede electrónica o de forma presencial.",
        "ca-valencia":
          "L'empadronament el gestiona el teu ajuntament, en la seua seu electrònica o presencialment.",
      },
      {
        es: "Para hacerlo por internet suele hacer falta identificarte con Cl@ve o certificado digital.",
        "ca-valencia":
          "Per a fer-ho per internet sol caldre identificar-te amb Cl@ve o certificat digital.",
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
      "En Castilla y León la ITV la gestionan estaciones concesionarias (ITEVELESA, TÜV SÜD y otras). La cita se pide en la web de tu estación; ten a mano la matrícula y el permiso de circulación. En la web de la Junta encuentras el listado de estaciones por provincia.",
    source: {
      organismo: "Junta de Castilla y León",
      title: "Inspección técnica de vehículos (ITV)",
      url: "https://economia.jcyl.es/web/es/industria/inspeccion-tecnica-vehiculos.html",
      fetched_at: "2026-07-22",
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
      "Si tu tarjeta sanitaria de Castilla y León se ha perdido o roto, puedes solicitar una nueva por internet en la web de Sacyl. Necesitas el número de tarjeta sanitaria, o bien el DNI y la fecha de nacimiento. La nueva tarjeta se recibe en el plazo indicado por Sacyl.",
    source: {
      organismo: "Sanidad de Castilla y León (Sacyl)",
      title: "Tarjeta sanitaria",
      url: "https://www.saludcastillayleon.es/es/serviciosonline/tarjeta-sanitaria",
      fetched_at: "2026-07-22",
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
      "El certificado o volante de empadronamiento lo expide tu ayuntamiento. Muchos lo ofrecen por su sede electrónica identificándote con Cl@ve o certificado digital, y también puedes pedirlo presencialmente. Consulta la web de tu ayuntamiento para ver cómo hacerlo.",
    source: {
      organismo: "Junta de Castilla y León",
      title: "Sede electrónica y trámites",
      url: "https://www.tramitacastillayleon.jcyl.es/web/es/tramites-servicios.html",
      fetched_at: "2026-07-22",
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
      "Puedes pedir cita con tu médico o enfermera de atención primaria en la web de Sacyl (cita.saludcastillayleon.es), en la app Sacyl Conecta, por teléfono o en el mostrador de tu centro de salud. Ten a mano tu tarjeta sanitaria de Castilla y León.",
    source: {
      organismo: "Sanidad de Castilla y León (Sacyl)",
      title: "Cita previa con su centro de salud",
      url: "https://www.saludcastillayleon.es/es/citaprevia",
      fetched_at: "2026-07-22",
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
      [/\b(empadronamiento|empadronament|padron|padro\b|volante|volant)/, "REQUEST_CENSUS_CERTIFICATE", "padron.certificado"],
      [/\b(tarjeta sanitaria|targeta sanitaria|sip)\b/, "RENEW_HEALTH_CARD", "sacyl.health.card"],
      [/\b(medic|metge|salud|salut|doctor|ambulatori|centro de salud)/, "BOOK_HEALTH_APPOINTMENT", "sacyl.health.primary-care"],
      [/\b(itv|inspeccion tecnica|inspeccio tecnica)/, "BOOK_ITV_APPOINTMENT", "jcyl.itv.info"],
      [/\b(carne\w? de conducir|carnet de conduir|permiso de conducir|permis de conduir|trafico|transit|dgt|canje|bescanvi)/, "BOOK_DGT_APPOINTMENT", "dgt.cita-previa"],
      [/\b(coche|cotxe|moto|vehicul|vehicle)/, "BOOK_ITV_APPOINTMENT", "jcyl.itv.info"],
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
    if (procedureId === "demo.worker.appointment") {
      // El worker prepara y cede: nunca "completed", siempre handoff.
      return {
        status: "user_handoff",
        receipt: {
          url: "https://portal-de-pruebas.example/cita",
          pending: "captcha, confirmar",
        },
        message: null,
      };
    }
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

  explainLetter: async (
    _sessionId: string,
    imageBase64: string,
    _mimeType: "image/png" | "image/jpeg",
    language: Lang,
  ): Promise<LetterAnalysis> => {
    const es = language === "es";
    // Se alterna entre carta de riesgo y carta rutinaria según el tamaño de
    // la imagen, para que la demostración enseñe ambos caminos.
    const highRisk = imageBase64.length % 2 === 0;
    const disclaimer = es
      ? "Esta es una lectura automática y puede contener errores. No es asesoramiento jurídico. Consulta siempre el documento original."
      : "Esta és una lectura automàtica i pot contindre errors. No és assessorament jurídic. Consulta sempre el document original.";
    const humanAdvice = es
      ? "Por su contenido, es mejor que te ayude una persona. Pide ayuda al personal del centro o acude a la oficina del organismo que firma la carta."
      : "Pel seu contingut, és millor que t'ajude una persona. Demana ajuda al personal del centre o acudix a l'oficina de l'organisme que firma la carta.";

    if (highRisk) {
      return {
        letter_id: `demo-letter-${Math.random().toString(36).slice(2, 8)}`,
        transcription_confidence: 0.88,
        facts: {
          organismo: "AGENCIA ESTATAL DE ADMINISTRACIÓN TRIBUTARIA",
          deadlines: [es ? "1 mes" : "1 mes"],
          sensitive_data: ["dni", "importe", "expediente"],
          excerpt:
            "AGENCIA ESTATAL DE ADMINISTRACIÓN TRIBUTARIA. PROVIDENCIA DE APREMIO. No habiéndose satisfecho la deuda en periodo voluntario, se inicia la vía ejecutiva. Podrá interponer recurso de reposición en el plazo de un mes. De no atender este requerimiento se procederá al embargo de bienes.",
        },
        explanation: {
          summary: es
            ? "Esta carta la envía AGENCIA ESTATAL DE ADMINISTRACIÓN TRIBUTARIA. Menciona un embargo, un procedimiento de apremio, la vía ejecutiva, un recurso, una deuda y un requerimiento. Es un asunto importante. Aparece un plazo: 1 mes. El documento contiene datos personales (tu DNI, un importe de dinero, un número de expediente): no lo dejes olvidado aquí."
            : "Esta carta l'envia AGENCIA ESTATAL DE ADMINISTRACIÓN TRIBUTARIA. Menciona un embargament, un procediment de constrenyiment, la via executiva, un recurs, un deute i un requeriment. És un assumpte important. Apareix un termini: 1 mes. El document conté dades personals (el teu DNI, un import de diners, un número d'expedient): no el deixes oblidat ací.",
          risk_level: "high",
          risk_terms: ["apremio", "deuda", "embargo", "recurso", "requerimiento", "via_ejecutiva"],
          ambiguous_deadline: false,
          recommend_human: true,
          human_advice: humanAdvice,
          disclaimer,
        },
      };
    }

    return {
      letter_id: `demo-letter-${Math.random().toString(36).slice(2, 8)}`,
      transcription_confidence: 0.91,
      facts: {
        organismo: "GERENCIA REGIONAL DE SALUD DE CASTILLA Y LEÓN (SACYL)",
        deadlines: ["30/09/2026"],
        sensitive_data: ["telefono"],
        excerpt:
          "GERENCIA REGIONAL DE SALUD DE CASTILLA Y LEÓN. Le informamos de que su cita de revisión ha quedado asignada en su centro de salud. Debe presentarse hasta el 30/09/2026 aportando su tarjeta sanitaria.",
      },
      explanation: {
        summary: es
          ? "Esta carta la envía la GERENCIA REGIONAL DE SALUD DE CASTILLA Y LEÓN. Aparece un plazo: 30/09/2026. El documento contiene datos personales (un teléfono): no lo dejes olvidado aquí."
          : "Esta carta l'envia la GERENCIA REGIONAL DE SALUD DE CASTILLA Y LEÓN. Apareix un termini: 30/09/2026. El document conté dades personals (un telèfon): no el deixes oblidat ací.",
        risk_level: "normal",
        risk_terms: [],
        ambiguous_deadline: false,
        recommend_human: false,
        human_advice: null,
        disclaimer,
      },
    };
  },

  purgeLetter: async (): Promise<void> => undefined,

  transcribeAudio: async (
    _sessionId: string,
    audioBase64: string,
    _mimeType: string,
    language: Lang,
  ): Promise<TranscriptResponse> => {
    // Frases de ejemplo, iguales que las del gateway mock del backend.
    const samples =
      language === "es"
        ? [
            { text: "quiero pedir cita para el médico", confidence: 0.94 },
            { text: "necesito renovar el dni", confidence: 0.91 },
            { text: "tengo que pasar la itv del coche", confidence: 0.89 },
          ]
        : [
            { text: "vull demanar cita amb el metge", confidence: 0.93 },
            { text: "necessite renovar el dni", confidence: 0.9 },
            { text: "he de passar la itv del cotxe", confidence: 0.88 },
          ];
    const sample = samples[audioBase64.length % samples.length];
    return { ...sample, usable: sample.confidence >= 0.6 };
  },

  printReceipt: async (): Promise<{ job_id: string }> => ({ job_id: "demo-print" }),
};

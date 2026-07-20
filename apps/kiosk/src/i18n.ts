// Textos del kiosco en castellano y valenciano. Regla del PRD: i18n desde el
// primer componente; ninguna cadena visible se escribe directamente en JSX.

export type Lang = "es" | "ca-valencia";

type Strings = {
  appName: string;
  chooseLanguage: string;
  languageEs: string;
  languageVa: string;
  homeTitle: string;
  homeSubtitle: string;
  searchPlaceholder: string;
  searchButton: string;
  searchHint: string;
  statusAvailable: string;
  statusComingSoon: string;
  back: string;
  endSession: string;
  endSessionConfirmTitle: string;
  endSessionConfirmBody: string;
  endSessionConfirmYes: string;
  endSessionConfirmNo: string;
  sessionEndedTitle: string;
  sessionEndedBody: string;
  requirementsTitle: string;
  officialSourcesTitle: string;
  comingSoonBanner: string;
  comingSoonHelp: string;
  assistedModeNote: string;
  informationModeNote: string;
  confirmAndRun: string;
  executionDone: string;
  receiptReference: string;
  printReceipt: string;
  printed: string;
  inactivityTitle: string;
  inactivityBody: string;
  inactivityStay: string;
  fontSize: string;
  highContrast: string;
  loading: string;
  apiError: string;
  scanTitle: string;
  scanIntro: string;
  scanButton: string;
  scanning: string;
  reviewTitle: string;
  reviewIntro: string;
  fieldReview: string;
  fieldInvalid: string;
  confirmData: string;
  dataConfirmed: string;
  rescan: string;
  fieldLabels: Record<string, string>;
  askTitle: string;
  askPlaceholder: string;
  askButton: string;
  askSourceLabel: string;
  askUpdatedLabel: string;
  askDisclaimer: string;
  askNoAnswer: string;
  claim: string;
  demoBadge: string;
  uploadPhoto: string;
  takePhoto: string;
  retakePhoto: string;
  usePhoto: string;
  cancelCapture: string;
  cameraStarting: string;
  cameraError: string;
  captureFrameHint: string;
  letterEntryTitle: string;
  letterEntryBody: string;
  letterEntryButton: string;
  letterTitle: string;
  letterIntro: string;
  letterStart: string;
  letterReading: string;
  letterFactsTitle: string;
  letterOrganismo: string;
  letterDeadlines: string;
  letterSensitive: string;
  letterExcerptTitle: string;
  letterExplanationTitle: string;
  letterHighRisk: string;
  letterAnother: string;
  letterDone: string;
  letterPurged: string;
  sensitiveLabels: Record<string, string>;
};

const es: Strings = {
  appName: "Tramitatrón",
  chooseLanguage: "Elige tu idioma",
  languageEs: "Castellano",
  languageVa: "Valencià",
  homeTitle: "¿Qué trámite necesitas hacer?",
  homeSubtitle: "Toca un trámite o escribe lo que necesitas.",
  searchPlaceholder: "Por ejemplo: quiero pedir cita para el médico",
  searchButton: "Buscar",
  searchHint: "También puedes tocar directamente uno de los trámites de abajo.",
  statusAvailable: "Disponible",
  statusComingSoon: "Próximamente",
  back: "Atrás",
  endSession: "Terminar y borrar mis datos",
  endSessionConfirmTitle: "¿Quieres terminar?",
  endSessionConfirmBody: "Se borrarán todos los datos de esta sesión.",
  endSessionConfirmYes: "Sí, terminar y borrar",
  endSessionConfirmNo: "No, seguir",
  sessionEndedTitle: "Sesión terminada",
  sessionEndedBody:
    "La sesión ha terminado y tus datos se han eliminado de este punto de atención.",
  requirementsTitle: "Qué necesitas",
  officialSourcesTitle: "Fuente oficial",
  comingSoonBanner: "Este trámite estará disponible próximamente en este punto.",
  comingSoonHelp:
    "Mientras tanto, puedes hacerlo en la web oficial o pedir ayuda al personal del centro.",
  assistedModeNote:
    "Este es un trámite asistido: el sistema te guía y tú confirmas cada paso importante.",
  informationModeNote:
    "Este es un trámite informativo: aquí te explicamos cómo hacerlo, y se completa en la web oficial o presencialmente.",
  confirmAndRun: "Confirmar y hacer la demostración",
  executionDone: "Demostración completada",
  receiptReference: "Referencia",
  printReceipt: "Imprimir justificante",
  printed: "Enviado a la impresora",
  inactivityTitle: "¿Sigues ahí?",
  inactivityBody: "Por tu seguridad, la sesión se cerrará y tus datos se borrarán.",
  inactivityStay: "Sí, sigo aquí",
  fontSize: "Tamaño de letra",
  highContrast: "Alto contraste",
  loading: "Cargando…",
  apiError: "No se ha podido conectar con el servicio. Pide ayuda al personal.",
  scanTitle: "Tu documento",
  scanIntro:
    "Para leer tu documento usaremos la cámara. Usaremos tus datos solo durante esta sesión: podrás revisarlos antes de continuar y se borrarán cuando termines.",
  scanButton: "Aceptar y usar la cámara",
  scanning: "Leyendo el documento…",
  reviewTitle: "Comprueba tus datos",
  reviewIntro: "Revisa que todo es correcto. Toca un campo para corregirlo.",
  fieldReview: "Revisa este dato",
  fieldInvalid: "Este dato no es válido",
  confirmData: "Los datos son correctos",
  dataConfirmed: "Datos confirmados. Se borrarán al terminar la sesión.",
  rescan: "Volver a escanear",
  fieldLabels: {
    dni_number: "Número de DNI o NIE",
    full_name: "Nombre y apellidos",
    birth_date: "Fecha de nacimiento (AAAA-MM-DD)",
    sip_number: "Número SIP",
  },
  askTitle: "¿Tienes alguna duda?",
  askPlaceholder: "Por ejemplo: ¿qué documentos necesito?",
  askButton: "Preguntar",
  askSourceLabel: "Fuente",
  askUpdatedLabel: "Consultado el",
  askDisclaimer:
    "Este texto procede de la fuente oficial indicada y puede haber cambiado. Compruébalo en el enlace.",
  askNoAnswer:
    "No he encontrado esa información en las fuentes oficiales. Consulta el enlace oficial o pide ayuda al personal.",
  claim: "Tus trámites, paso a paso.",
  demoBadge: "Modo demostración · datos de ejemplo",
  uploadPhoto: "O subir una foto del documento",
  takePhoto: "Hacer la foto",
  retakePhoto: "Repetir la foto",
  usePhoto: "Usar esta foto",
  cancelCapture: "Cancelar",
  cameraStarting: "Encendiendo la cámara…",
  cameraError: "No se ha podido usar la cámara. Puedes subir una foto del documento.",
  captureFrameHint:
    "Coloca el documento dentro del recuadro, sin reflejos y con las cuatro esquinas visibles.",
  letterEntryTitle: "¿Has recibido una carta y no la entiendes?",
  letterEntryBody: "Te la leemos y te la explicamos con palabras sencillas.",
  letterEntryButton: "Entender una carta",
  letterTitle: "Entender una carta",
  letterIntro:
    "Haz una foto de la carta. La leeremos solo durante esta sesión y se borrará cuando termines. No guardamos ninguna copia.",
  letterStart: "📷 Hacer la foto de la carta",
  letterReading: "Leyendo la carta…",
  letterFactsTitle: "Lo que pone la carta",
  letterOrganismo: "Quién la envía",
  letterDeadlines: "Plazo que aparece",
  letterSensitive: "Contiene datos personales",
  letterExcerptTitle: "Texto leído",
  letterExplanationTitle: "Lo que entendemos nosotros",
  letterHighRisk: "Es mejor que te ayude una persona",
  letterAnother: "Leer otra carta",
  letterDone: "Terminar",
  letterPurged: "La carta se ha borrado.",
  sensitiveLabels: {
    dni: "DNI",
    nie: "NIE",
    iban: "número de cuenta",
    telefono: "teléfono",
    email: "correo electrónico",
    importe: "importe de dinero",
    expediente: "número de expediente",
  },
};

const va: Strings = {
  appName: "Tramitatrón",
  chooseLanguage: "Tria el teu idioma",
  languageEs: "Castellano",
  languageVa: "Valencià",
  homeTitle: "Quin tràmit necessites fer?",
  homeSubtitle: "Toca un tràmit o escriu el que necessites.",
  searchPlaceholder: "Per exemple: vull demanar cita per al metge",
  searchButton: "Buscar",
  searchHint: "També pots tocar directament un dels tràmits de baix.",
  statusAvailable: "Disponible",
  statusComingSoon: "Pròximament",
  back: "Arrere",
  endSession: "Acabar i esborrar les meues dades",
  endSessionConfirmTitle: "Vols acabar?",
  endSessionConfirmBody: "S'esborraran totes les dades d'esta sessió.",
  endSessionConfirmYes: "Sí, acabar i esborrar",
  endSessionConfirmNo: "No, continuar",
  sessionEndedTitle: "Sessió acabada",
  sessionEndedBody:
    "La sessió ha acabat i les teues dades s'han eliminat d'este punt d'atenció.",
  requirementsTitle: "Què necessites",
  officialSourcesTitle: "Font oficial",
  comingSoonBanner: "Este tràmit estarà disponible pròximament en este punt.",
  comingSoonHelp:
    "Mentrestant, pots fer-lo en la web oficial o demanar ajuda al personal del centre.",
  assistedModeNote:
    "Este és un tràmit assistit: el sistema et guia i tu confirmes cada pas important.",
  informationModeNote:
    "Este és un tràmit informatiu: ací t'expliquem com fer-lo, i es completa en la web oficial o presencialment.",
  confirmAndRun: "Confirmar i fer la demostració",
  executionDone: "Demostració completada",
  receiptReference: "Referència",
  printReceipt: "Imprimir justificant",
  printed: "Enviat a la impressora",
  inactivityTitle: "Continues ací?",
  inactivityBody: "Per la teua seguretat, la sessió es tancarà i les teues dades s'esborraran.",
  inactivityStay: "Sí, continue ací",
  fontSize: "Grandària de lletra",
  highContrast: "Alt contrast",
  loading: "Carregant…",
  apiError: "No s'ha pogut connectar amb el servici. Demana ajuda al personal.",
  scanTitle: "El teu document",
  scanIntro:
    "Per a llegir el teu document usarem la càmera. Usarem les teues dades només durant esta sessió: podràs revisar-les abans de continuar i s'esborraran quan acabes.",
  scanButton: "Acceptar i usar la càmera",
  scanning: "Llegint el document…",
  reviewTitle: "Comprova les teues dades",
  reviewIntro: "Revisa que tot és correcte. Toca un camp per a corregir-lo.",
  fieldReview: "Revisa esta dada",
  fieldInvalid: "Esta dada no és vàlida",
  confirmData: "Les dades són correctes",
  dataConfirmed: "Dades confirmades. S'esborraran quan acabe la sessió.",
  rescan: "Tornar a escanejar",
  fieldLabels: {
    dni_number: "Número de DNI o NIE",
    full_name: "Nom i cognoms",
    birth_date: "Data de naixement (AAAA-MM-DD)",
    sip_number: "Número SIP",
  },
  askTitle: "Tens algun dubte?",
  askPlaceholder: "Per exemple: quins documents necessite?",
  askButton: "Preguntar",
  askSourceLabel: "Font",
  askUpdatedLabel: "Consultat el",
  askDisclaimer:
    "Este text procedix de la font oficial indicada i pot haver canviat. Comprova-ho en l'enllaç.",
  askNoAnswer:
    "No he trobat eixa informació en les fonts oficials. Consulta l'enllaç oficial o demana ajuda al personal.",
  claim: "Els teus tràmits, pas a pas.",
  demoBadge: "Mode demostració · dades d'exemple",
  uploadPhoto: "O pujar una foto del document",
  takePhoto: "Fer la foto",
  retakePhoto: "Repetir la foto",
  usePhoto: "Usar esta foto",
  cancelCapture: "Cancel·lar",
  cameraStarting: "Encenent la càmera…",
  cameraError: "No s'ha pogut usar la càmera. Pots pujar una foto del document.",
  captureFrameHint:
    "Col·loca el document dins del requadre, sense reflexos i amb les quatre cantonades visibles.",
  letterEntryTitle: "Has rebut una carta i no l'entens?",
  letterEntryBody: "Te la llegim i te l'expliquem amb paraules senzilles.",
  letterEntryButton: "Entendre una carta",
  letterTitle: "Entendre una carta",
  letterIntro:
    "Fes una foto de la carta. La llegirem només durant esta sessió i s'esborrarà quan acabes. No guardem cap còpia.",
  letterStart: "📷 Fer la foto de la carta",
  letterReading: "Llegint la carta…",
  letterFactsTitle: "El que diu la carta",
  letterOrganismo: "Qui l'envia",
  letterDeadlines: "Termini que apareix",
  letterSensitive: "Conté dades personals",
  letterExcerptTitle: "Text llegit",
  letterExplanationTitle: "El que entenem nosaltres",
  letterHighRisk: "És millor que t'ajude una persona",
  letterAnother: "Llegir una altra carta",
  letterDone: "Acabar",
  letterPurged: "La carta s'ha esborrat.",
  sensitiveLabels: {
    dni: "DNI",
    nie: "NIE",
    iban: "número de compte",
    telefono: "telèfon",
    email: "correu electrònic",
    importe: "import de diners",
    expediente: "número d'expedient",
  },
};

const STRINGS: Record<Lang, Strings> = { es, "ca-valencia": va };

export function t(lang: Lang): Strings {
  return STRINGS[lang];
}

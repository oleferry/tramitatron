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
};

const es: Strings = {
  appName: "Tramitatrón",
  chooseLanguage: "Elige tu idioma",
  languageEs: "Castellano",
  languageVa: "Valencià",
  homeTitle: "¿Qué necesitas hacer?",
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
  sessionEndedBody: "Tus datos se han borrado. Gracias por usar el servicio.",
  requirementsTitle: "Qué necesitas",
  officialSourcesTitle: "Fuente oficial",
  comingSoonBanner: "Este trámite estará disponible próximamente en este punto.",
  comingSoonHelp:
    "Mientras tanto, puedes hacerlo en la web oficial o pedir ayuda al personal del centro.",
  assistedModeNote:
    "Este es un trámite asistido: el sistema te guía y tú confirmas cada paso importante.",
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
    "Vamos a leer los datos de tu documento con la cámara. Después podrás revisarlos y corregirlos antes de usarlos.",
  scanButton: "Escanear documento",
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
};

const va: Strings = {
  appName: "Tramitatrón",
  chooseLanguage: "Tria el teu idioma",
  languageEs: "Castellano",
  languageVa: "Valencià",
  homeTitle: "Què necessites fer?",
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
  sessionEndedBody: "Les teues dades s'han esborrat. Gràcies per usar el servici.",
  requirementsTitle: "Què necessites",
  officialSourcesTitle: "Font oficial",
  comingSoonBanner: "Este tràmit estarà disponible pròximament en este punt.",
  comingSoonHelp:
    "Mentrestant, pots fer-lo en la web oficial o demanar ajuda al personal del centre.",
  assistedModeNote:
    "Este és un tràmit assistit: el sistema et guia i tu confirmes cada pas important.",
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
    "Llegirem les dades del teu document amb la càmera. Després podràs revisar-les i corregir-les abans d'usar-les.",
  scanButton: "Escanejar document",
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
};

const STRINGS: Record<Lang, Strings> = { es, "ca-valencia": va };

export function t(lang: Lang): Strings {
  return STRINGS[lang];
}

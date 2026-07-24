// Datos del despliegue que dependen de la administración que instala el tótem,
// no del código. Se fijan por variable de build (como VITE_LOCALES). El aviso de
// privacidad (art. 13 RGPD) necesita nombrar al RESPONSABLE del tratamiento y un
// CONTACTO; por defecto se usan fórmulas genéricas para no afirmar nada falso.

// Responsable del tratamiento: la administración titular del punto de atención.
export const CONTROLLER_NAME: string =
  import.meta.env.VITE_CONTROLLER_NAME || "la administración de este punto de atención";

// Contacto para privacidad / DPD. Por defecto, el personal presente (siempre
// existe); un despliegue puede poner un correo o teléfono del DPD.
export const PRIVACY_CONTACT: string =
  import.meta.env.VITE_PRIVACY_CONTACT || "el personal del centro de atención";

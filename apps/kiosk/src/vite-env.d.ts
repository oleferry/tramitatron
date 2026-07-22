/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Idiomas activos en el despliegue, separados por comas (p. ej. "es" o "es,ca-valencia"). */
  readonly VITE_LOCALES?: string;
  /** Identificador de este tótem en el parque (TT-601), p. ej. "cyl-valladolid-01". */
  readonly VITE_TOTEM_ID?: string;
  /** Versión desplegada del kiosco, para el latido del tótem. */
  readonly VITE_APP_VERSION?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

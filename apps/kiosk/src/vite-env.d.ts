/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Idiomas activos en el despliegue, separados por comas (p. ej. "es" o "es,ca-valencia"). */
  readonly VITE_LOCALES?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

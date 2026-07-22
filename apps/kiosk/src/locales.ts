import type { Lang } from "./i18n";

// Idiomas activos en ESTE despliegue. Por defecto, ambos: la i18n vive desde el
// primer componente (regla 9 del proyecto) y no se toca. Un despliegue
// monolingüe —por ejemplo, un piloto en una comunidad sin lengua cooficial como
// Castilla y León— los limita con la variable de build VITE_LOCALES=es.
//
// Con un solo idioma activo, el kiosco OMITE la pantalla de selección y arranca
// directamente en ese idioma. Volver a activar el valenciano es cambiar el valor
// de VITE_LOCALES, sin tocar código.
const ALL: Lang[] = ["es", "ca-valencia"];

function resolveLocales(): Lang[] {
  const raw = import.meta.env.VITE_LOCALES;
  if (!raw) return ALL;
  const wanted = raw.split(",").map((s) => s.trim());
  const filtered = ALL.filter((l) => wanted.includes(l));
  return filtered.length > 0 ? filtered : ["es"];
}

export const LOCALES: Lang[] = resolveLocales();

/** Si solo hay un idioma activo, se fuerza ese y no se muestra el selector. */
export const FORCED_LANG: Lang | null = LOCALES.length === 1 ? LOCALES[0] : null;

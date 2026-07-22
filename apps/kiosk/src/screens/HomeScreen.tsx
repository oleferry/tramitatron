import { useEffect, useState } from "react";

import type { CatalogItem } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { procedureIcon } from "../icons";
import { VoiceInput } from "./VoiceInput";

// Normaliza para comparar sin distinguir mayúsculas ni acentos ("médico" =
// "medico"), para que el filtro en vivo sea tolerante a cómo se escriba.
function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, ""); // quita las marcas diacríticas combinantes
}

export function HomeScreen({
  lang,
  sessionId,
  voiceEnabled,
  onOpenProcedure,
  onOpenLetter,
}: {
  lang: Lang;
  sessionId: string;
  voiceEnabled: boolean;
  onOpenProcedure: (id: string) => void;
  onOpenLetter: () => void;
}) {
  const strings = t(lang);
  const [catalog, setCatalog] = useState<CatalogItem[] | null>(null);
  const [query, setQuery] = useState("");
  const [clarification, setClarification] = useState<string | null>(null);
  const [highlighted, setHighlighted] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    api
      .getCatalog()
      .then(setCatalog)
      .catch(() => setFailed(true));
  }, []);

  // Coincidencias por palabra clave (sin IA): cada palabra del texto debe
  // aparecer en el nombre o la descripción del trámite (AND), sin acentos.
  const keywordMatches = (text: string): CatalogItem[] => {
    const q = normalize(text.trim());
    if (!q || !catalog) return [];
    return catalog.filter((item) => {
      const haystack = normalize(item.name[lang] + " " + (item.description?.[lang] ?? ""));
      return q.split(/\s+/).every((word) => haystack.includes(word));
    });
  };

  // Acepta el texto por parámetro: al confirmar una transcripción hay que
  // buscar con ella, no con el valor que tuviera el input en ese render.
  const search = async (spoken?: string) => {
    const text = (spoken ?? query).trim();
    if (!text) return;
    setClarification(null);
    setHighlighted(null);
    // Atajo: si las palabras clave dejan un único trámite, se abre directo, sin
    // IA (instantáneo y funciona sin red). Solo se consulta a la IA si hay
    // ambigüedad (varias o ninguna coincidencia literal).
    const matches = keywordMatches(text);
    if (matches.length === 1) {
      onOpenProcedure(matches[0].id);
      return;
    }
    try {
      const result = await api.classifyIntent(text, lang);
      if (result.next_action === "SHOW_PROCEDURE" && result.procedure_id) {
        setHighlighted(result.procedure_id);
        onOpenProcedure(result.procedure_id);
      } else {
        setClarification(result.clarification ?? strings.apiError);
      }
    } catch {
      setFailed(true);
    }
  };

  // Filtro EN VIVO por palabras clave (sin IA, instantáneo): estrecha las
  // tarjetas visibles mientras se escribe. El botón «Buscar» sigue usando la IA
  // para frases en lenguaje natural.
  const trimmed = query.trim();
  const filtered = catalog ? (trimmed ? keywordMatches(trimmed) : catalog) : [];

  // Mensaje para lector de pantalla: cuántos trámites quedan al filtrar. Solo
  // cuando hay búsqueda escrita (anunciar el catálogo entero al cargar sería
  // ruido). El aviso visible «sin coincidencias» ya se muestra aparte abajo.
  const resultsAnnouncement =
    trimmed && catalog
      ? filtered.length === 0
        ? strings.searchNoMatch
        : filtered.length === 1
          ? strings.searchResultsOne
          : strings.searchResultsMany.replace("{n}", String(filtered.length))
      : "";

  return (
    <div className="screen">
      <h2>{strings.homeTitle}</h2>
      <p className="subtitle">{strings.homeSubtitle}</p>

      <div className="search-row">
        <span className="search-icon" aria-hidden="true">
          🔎
        </span>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && void search()}
          placeholder={strings.searchPlaceholder}
          aria-label={strings.searchPlaceholder}
        />
        <button className="btn-primary" onClick={() => void search()}>
          {strings.searchButton}
        </button>
      </div>

      {/* La voz acompaña al buscador; nunca lo sustituye (PRD §14.3). */}
      {voiceEnabled && (
        <VoiceInput
          lang={lang}
          sessionId={sessionId}
          onConfirmed={(text) => {
            setQuery(text);
            void search(text);
          }}
        />
      )}

      {/* Caso D del PRD: entrar por "tengo una carta" es tan legítimo como
          buscar un trámite, así que va al mismo nivel que el buscador. */}
      <button className="letter-entry" onClick={onOpenLetter}>
        <span className="card-icon" aria-hidden="true">
          ✉️
        </span>
        <span className="letter-entry-text">
          <strong>{strings.letterEntryTitle}</strong>
          <span>{strings.letterEntryBody}</span>
        </span>
        <span className="letter-entry-cta">{strings.letterEntryButton}</span>
      </button>

      {/* Región de estado (invisible): anuncia al lector de pantalla cuántos
          trámites deja el filtro en vivo (WCAG 2.2 §4.1.3, mensajes de estado). */}
      <p className="sr-only" role="status" aria-live="polite">
        {resultsAnnouncement}
      </p>

      {/* role="status": la aclaración de la IA llega tras una búsqueda asíncrona
          y debe anunciarse al aparecer, no solo verse. */}
      {clarification && (
        <div className="clarification" role="status">
          {clarification}
        </div>
      )}
      {failed && <div className="banner banner-info">{strings.apiError}</div>}
      {!catalog && !failed && <p className="subtitle">{strings.loading}</p>}

      {catalog &&
        (trimmed && filtered.length === 0 ? (
          <p className="subtitle">{strings.searchNoMatch}</p>
        ) : (
          <>
            <p className="subtitle">{strings.searchHint}</p>
            <div className="cards">
              {filtered.map((item) => (
                <button
                  key={item.id}
                  className={`card${highlighted === item.id ? " highlighted" : ""}`}
                  onClick={() => onOpenProcedure(item.id)}
                >
                  <div className="card-top">
                    <span className="card-icon" aria-hidden="true">
                      {procedureIcon(item.id)}
                    </span>
                    <span
                      className={`badge ${
                        item.status === "available" ? "badge-available" : "badge-coming"
                      }`}
                    >
                      {item.status === "available"
                        ? strings.statusAvailable
                        : strings.statusComingSoon}
                    </span>
                  </div>
                  <h3>{item.name[lang]}</h3>
                  {item.description && <p>{item.description[lang]}</p>}
                </button>
              ))}
            </div>
          </>
        ))}
    </div>
  );
}

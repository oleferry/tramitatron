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

  // Acepta el texto por parámetro: al confirmar una transcripción hay que
  // buscar con ella, no con el valor que tuviera el input en ese render.
  const search = async (spoken?: string) => {
    const text = (spoken ?? query).trim();
    if (!text) return;
    setClarification(null);
    setHighlighted(null);
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

      {clarification && <div className="clarification">{clarification}</div>}
      {failed && <div className="banner banner-info">{strings.apiError}</div>}
      {!catalog && !failed && <p className="subtitle">{strings.loading}</p>}

      {catalog &&
        (() => {
          // Filtro EN VIVO por palabras clave (sin IA, instantáneo): estrecha
          // las tarjetas visibles mientras se escribe. El botón «Buscar» sigue
          // usando la IA para frases en lenguaje natural.
          const q = normalize(query.trim());
          const filtered = q
            ? catalog.filter((item) => {
                const haystack = normalize(
                  item.name[lang] + " " + (item.description?.[lang] ?? ""),
                );
                return q.split(/\s+/).every((word) => haystack.includes(word));
              })
            : catalog;

          if (q && filtered.length === 0) {
            return <p className="subtitle">{strings.searchNoMatch}</p>;
          }

          return (
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
          );
        })()}
    </div>
  );
}

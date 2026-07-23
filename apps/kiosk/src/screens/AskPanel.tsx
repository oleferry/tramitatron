import { useState } from "react";

import type { AskResponse } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";

// Preguntas sobre un trámite: la respuesta es un extracto literal de la
// fuente oficial, siempre con organismo, fecha de consulta y enlace (PRD §16.3).
export function AskPanel({
  lang,
  procedureId,
}: {
  lang: Lang;
  procedureId: string;
}) {
  const strings = t(lang);
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);

  const ask = async () => {
    const text = question.trim();
    if (!text || loading) return;
    setLoading(true);
    setFailed(false);
    try {
      setResult(await api.ask(text, lang, procedureId));
    } catch {
      setFailed(true);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel">
      <h3>
        <span aria-hidden="true">💬</span> {strings.askTitle}
      </h3>
      <div className="doc-step" aria-busy={loading}>
        <div className="search-row">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void ask()}
            placeholder={strings.askPlaceholder}
            aria-label={strings.askPlaceholder}
          />
          {/* aria-label fijo: mientras carga el texto es "…", que el lector
              leería como "puntos suspensivos"; el nombre accesible no cambia. */}
          <button
            className="btn-primary"
            onClick={() => void ask()}
            disabled={loading}
            aria-label={strings.askButton}
          >
            {loading ? "…" : strings.askButton}
          </button>
        </div>

        {/* Región viva SIEMPRE presente: la respuesta (o el "no encontrado" o el
            error) llega tras una llamada asíncrona y así se anuncia al aparecer,
            no solo se ve (WCAG 2.2 §4.1.3, mensajes de estado). */}
        <div aria-live="polite">
          {failed && <div className="banner banner-info">{strings.apiError}</div>}

          {result && !result.found && (
            <div className="clarification">{strings.askNoAnswer}</div>
          )}

          {result?.found && result.answer && result.source && (
            <div className="answer">
              <p className="answer-text">{result.answer}</p>
              <p className="answer-source">
                {strings.askSourceLabel}: <strong>{result.source.organismo}</strong> —{" "}
                {result.source.title}. {strings.askUpdatedLabel} {result.source.fetched_at}.
                <br />
                <span className="answer-url">{result.source.url}</span>
              </p>
              <p className="answer-disclaimer">{strings.askDisclaimer}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

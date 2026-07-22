import { useState } from "react";

import type { LetterAnalysis } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { CameraCapture } from "./CameraCapture";
import { ReadAloudButton } from "./ReadAloudButton";

type Phase = "idle" | "capture" | "reading" | "result" | "error";

/**
 * Explicación de cartas administrativas (TT-404, PRD §5.2 caso D).
 *
 * La pantalla separa visualmente dos bloques: lo que PONE la carta (hechos
 * leídos) y lo que ENTENDEMOS nosotros (lectura del sistema). Cuando el
 * backend marca riesgo alto, el aviso de acudir a una persona va arriba del
 * todo: es lo primero que debe ver alguien con una carta de embargo.
 */
export function LetterScreen({
  lang,
  sessionId,
  voiceEnabled,
  onClose,
}: {
  lang: Lang;
  sessionId: string;
  voiceEnabled: boolean;
  onClose: () => void;
}) {
  const strings = t(lang);
  const [phase, setPhase] = useState<Phase>("idle");
  const [analysis, setAnalysis] = useState<LetterAnalysis | null>(null);

  const analyze = async (base64: string, mime: "image/png" | "image/jpeg") => {
    setPhase("reading");
    try {
      setAnalysis(await api.explainLetter(sessionId, base64, mime, lang));
      setPhase("result");
    } catch {
      setPhase("error");
    }
  };

  const onFileChosen = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      void analyze(result.split(",")[1], file.type === "image/png" ? "image/png" : "image/jpeg");
    };
    reader.readAsDataURL(file);
  };

  // Borrado explícito: no se espera al fin de sesión para soltar la carta.
  const discardAndClose = async () => {
    if (analysis) {
      try {
        await api.purgeLetter(sessionId, analysis.letter_id);
      } catch {
        // La sesión se purgará igualmente al terminar; no bloquea al usuario.
      }
    }
    setAnalysis(null);
    onClose();
  };

  const restart = async () => {
    if (analysis) {
      try {
        await api.purgeLetter(sessionId, analysis.letter_id);
      } catch {
        // Igual que arriba: el TTL de la sesión es la red de seguridad.
      }
    }
    setAnalysis(null);
    setPhase("capture");
  };

  return (
    <div className="screen">
      <div className="language-hero" aria-hidden="true">
        ✉️
      </div>
      <h2>{strings.letterTitle}</h2>

      {phase === "idle" && (
        <div className="panel">
          <p className="subtitle">{strings.letterIntro}</p>
          <button className="btn-primary btn-xl" onClick={() => setPhase("capture")}>
            {strings.letterStart}
          </button>
          <label className="upload-fallback">
            {strings.uploadPhoto}
            <input type="file" accept="image/jpeg,image/png" onChange={onFileChosen} />
          </label>
        </div>
      )}

      {phase === "capture" && (
        <CameraCapture
          lang={lang}
          onCaptured={(base64, mime) => void analyze(base64, mime)}
          onCancel={() => setPhase("idle")}
        />
      )}

      {phase === "reading" && (
        <p className="subtitle" role="status">
          {strings.letterReading}
        </p>
      )}

      {phase === "error" && <div className="banner banner-info">{strings.apiError}</div>}

      {phase === "result" && analysis && (
        <>
          {analysis.explanation.recommend_human && (
            // role="alert": el aviso de acudir a una persona (p. ej. una carta de
            // embargo) se anuncia de inmediato al lector de pantalla.
            <div className="banner banner-warning" role="alert">
              <strong>⚠️ {strings.letterHighRisk}</strong>
              {analysis.explanation.human_advice && <p>{analysis.explanation.human_advice}</p>}
            </div>
          )}

          <div className="panel">
            <h3>
              <span aria-hidden="true">📄</span> {strings.letterFactsTitle}
            </h3>
            {analysis.facts.organismo && (
              <p>
                <strong>{strings.letterOrganismo}:</strong> {analysis.facts.organismo}
              </p>
            )}
            {analysis.facts.deadlines.length > 0 && (
              <p>
                <strong>{strings.letterDeadlines}:</strong>{" "}
                {analysis.facts.deadlines.join(" · ")}
              </p>
            )}
            {analysis.facts.sensitive_data.length > 0 && (
              <p>
                <strong>{strings.letterSensitive}:</strong>{" "}
                {analysis.facts.sensitive_data
                  .map((kind) => strings.sensitiveLabels[kind] ?? kind)
                  .join(", ")}
              </p>
            )}
            {analysis.facts.excerpt && (
              <details>
                <summary>{strings.letterExcerptTitle}</summary>
                <p className="letter-excerpt">{analysis.facts.excerpt}</p>
              </details>
            )}
          </div>

          <div className="panel">
            <h3>
              <span aria-hidden="true">💬</span> {strings.letterExplanationTitle}
            </h3>
            <p>{analysis.explanation.summary}</p>
            <p className="disclaimer">{analysis.explanation.disclaimer}</p>
            {/* Quien no entiende una carta a menudo tampoco la lee con
                comodidad: escucharla es aquí más útil que en ningún sitio. */}
            {voiceEnabled && (
              <ReadAloudButton
                lang={lang}
                text={[
                  analysis.explanation.recommend_human
                    ? analysis.explanation.human_advice ?? ""
                    : "",
                  analysis.explanation.summary,
                  analysis.explanation.disclaimer,
                ]
                  .filter(Boolean)
                  .join(" ")}
              />
            )}
          </div>

          <button className="btn-secondary" onClick={() => void restart()}>
            {strings.letterAnother}
          </button>
        </>
      )}

      <button className="btn-secondary" onClick={() => void discardAndClose()}>
        ← {strings.back}
      </button>
    </div>
  );
}

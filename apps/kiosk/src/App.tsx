import { useCallback, useEffect, useRef, useState } from "react";

import { api, metrics, telemetry } from "./api";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import { stopSpeaking } from "./speech";
import { BrandMark } from "./BrandMark";
import { FORCED_LANG } from "./locales";
import { HomeScreen } from "./screens/HomeScreen";
import { LanguageScreen } from "./screens/LanguageScreen";
import { LetterScreen } from "./screens/LetterScreen";
import { ProcedureScreen } from "./screens/ProcedureScreen";

// Tiempos de inactividad del kiosco (más cortos que el TTL del servidor):
// a los 90 s se avisa; 30 s después se purga la sesión.
const INACTIVITY_WARN_MS = 90_000;
const INACTIVITY_END_MS = 30_000;
const FONT_SCALES = [1, 1.25, 1.5];

type Screen =
  | { kind: "language" }
  | { kind: "home" }
  | { kind: "procedure"; procedureId: string }
  | { kind: "letter" }
  | { kind: "ended" };

export function App() {
  const [lang, setLang] = useState<Lang>("es");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [screen, setScreen] = useState<Screen>({ kind: "language" });
  const [fontScaleIdx, setFontScaleIdx] = useState(0);
  const [highContrast, setHighContrast] = useState(false);
  // La voz es un canal opcional y desactivable (PRD §14.3). Nunca es el
  // único: todo lo que se puede hacer hablando se puede hacer escribiendo.
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [confirmEndOpen, setConfirmEndOpen] = useState(false);
  const [inactivityWarn, setInactivityWarn] = useState(false);
  const [error, setError] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const [feedbackGiven, setFeedbackGiven] = useState(false);

  useEffect(() => {
    const onDemo = () => setDemoMode(true);
    window.addEventListener("tramitatron:demo", onDemo);
    return () => window.removeEventListener("tramitatron:demo", onDemo);
  }, []);

  // Latido del tótem (TT-601): al arrancar y cada 60 s, sin depender de que
  // haya una sesión abierta. A fuego y olvido; sin backend no hace nada.
  useEffect(() => {
    void telemetry.heartbeat();
    const id = window.setInterval(() => void telemetry.heartbeat(), 60_000);
    return () => window.clearInterval(id);
  }, []);

  const warnTimer = useRef<number | undefined>(undefined);
  const endTimer = useRef<number | undefined>(undefined);
  const sessionRef = useRef<string | null>(null);
  sessionRef.current = sessionId;
  // Pantalla actual, para saber si alguien cierra la sesión dentro de un
  // trámite (abandono real) frente a hacerlo desde el inicio.
  const screenRef = useRef<Screen>(screen);
  screenRef.current = screen;

  const strings = t(lang);

  const resetToStart = useCallback(() => {
    setSessionId(null);
    setConfirmEndOpen(false);
    setInactivityWarn(false);
    setScreen({ kind: "ended" });
    window.setTimeout(() => {
      setScreen({ kind: "language" });
      setFontScaleIdx(0);
      setHighContrast(false);
      setLang("es");
      setFeedbackGiven(false);
    }, 8000);
  }, []);

  const endSession = useCallback(async () => {
    // Al cerrar la sesión no puede quedar una voz leyendo datos del anterior.
    stopSpeaking();
    // Abandono: se cierra la sesión estando dentro de un trámite (métrica
    // agregada; solo el id del trámite, nada de la persona).
    const scr = screenRef.current;
    if (scr.kind === "procedure") metrics.procedureAbandoned(scr.procedureId);
    const current = sessionRef.current;
    if (current) {
      try {
        await api.endSession(current);
      } catch {
        // La purga del lado servidor caduca sola por TTL; seguimos con el reinicio local.
      }
    }
    resetToStart();
  }, [resetToStart]);

  // Guardia de inactividad: cualquier interacción reinicia los temporizadores.
  useEffect(() => {
    if (!sessionId) return;

    const armTimers = () => {
      window.clearTimeout(warnTimer.current);
      window.clearTimeout(endTimer.current);
      setInactivityWarn(false);
      warnTimer.current = window.setTimeout(() => {
        setInactivityWarn(true);
        endTimer.current = window.setTimeout(() => void endSession(), INACTIVITY_END_MS);
      }, INACTIVITY_WARN_MS);
    };

    const onActivity = () => {
      if (!inactivityWarn) armTimers();
    };

    armTimers();
    window.addEventListener("pointerdown", onActivity);
    window.addEventListener("keydown", onActivity);
    return () => {
      window.clearTimeout(warnTimer.current);
      window.clearTimeout(endTimer.current);
      window.removeEventListener("pointerdown", onActivity);
      window.removeEventListener("keydown", onActivity);
    };
  }, [sessionId, inactivityWarn, endSession]);

  const startSession = async (chosen: Lang) => {
    setLang(chosen);
    setError(false);
    try {
      const session = await api.createSession(chosen);
      setSessionId(session.session_id);
      setScreen({ kind: "home" });
    } catch {
      setError(true);
    }
  };

  // Despliegue monolingüe (p. ej. piloto en Castilla y León): no se muestra la
  // pantalla de idioma; se arranca directamente en el único idioma activo. Se
  // dispara al entrar en "language" (inicio y tras reiniciar entre personas).
  useEffect(() => {
    if (screen.kind === "language" && FORCED_LANG && !sessionRef.current) {
      void startSession(FORCED_LANG);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen.kind]);

  const stayHere = async () => {
    window.clearTimeout(endTimer.current);
    setInactivityWarn(false);
    if (sessionRef.current) {
      try {
        await api.extendSession(sessionRef.current);
      } catch {
        void endSession();
      }
    }
  };

  const goBack = () => {
    if (screen.kind === "procedure" || screen.kind === "letter") setScreen({ kind: "home" });
    else if (screen.kind === "home") setConfirmEndOpen(true);
  };

  return (
    <div
      className={`kiosk${highContrast ? " high-contrast" : ""}`}
      style={{ ["--font-scale" as string]: FONT_SCALES[fontScaleIdx] }}
    >
      <header className="kiosk-header">
        <div className="brand">
          <BrandMark className="brand-mark" />
          <h1>{strings.appName}</h1>
          {demoMode && <span className="demo-badge">{strings.demoBadge}</span>}
        </div>
        <div className="a11y-controls">
          <button
            className="btn-secondary btn-small"
            onClick={() => setFontScaleIdx((fontScaleIdx + 1) % FONT_SCALES.length)}
            aria-label={strings.fontSize}
          >
            A{fontScaleIdx > 0 ? "+".repeat(fontScaleIdx) : ""}
          </button>
          <button
            className="btn-secondary btn-small"
            onClick={() => setHighContrast(!highContrast)}
            aria-pressed={highContrast}
          >
            {strings.highContrast}
          </button>
          <button
            className="btn-secondary btn-small"
            onClick={() => {
              stopSpeaking();
              setVoiceEnabled(!voiceEnabled);
            }}
            aria-pressed={voiceEnabled}
          >
            {voiceEnabled ? "🔊" : "🔇"} {strings.voiceToggle}
          </button>
        </div>
      </header>

      <main className="kiosk-main">
        {error && <div className="banner banner-info">{strings.apiError}</div>}

        {screen.kind === "language" &&
          (FORCED_LANG ? (
            // Monolingüe: no se muestra el selector; se arranca solo (arriba).
            <p className="subtitle">{t(FORCED_LANG).loading}</p>
          ) : (
            <LanguageScreen onChoose={(l) => void startSession(l)} />
          ))}

        {screen.kind === "home" && sessionId && (
          <HomeScreen
            lang={lang}
            sessionId={sessionId}
            voiceEnabled={voiceEnabled}
            onOpenProcedure={(procedureId) => {
              metrics.procedureStarted(procedureId);
              setScreen({ kind: "procedure", procedureId });
            }}
            onOpenLetter={() => setScreen({ kind: "letter" })}
          />
        )}

        {screen.kind === "procedure" && sessionId && (
          <ProcedureScreen
            lang={lang}
            sessionId={sessionId}
            procedureId={screen.procedureId}
            voiceEnabled={voiceEnabled}
          />
        )}

        {screen.kind === "letter" && sessionId && (
          <LetterScreen
            lang={lang}
            sessionId={sessionId}
            voiceEnabled={voiceEnabled}
            onClose={() => setScreen({ kind: "home" })}
          />
        )}

        {screen.kind === "ended" && (
          <div className="centered-splash">
            <span className="splash-icon" aria-hidden="true">
              ✅
            </span>
            <h2>{strings.sessionEndedTitle}</h2>
            <p>{strings.sessionEndedBody}</p>
            {feedbackGiven ? (
              <p className="feedback-thanks">{strings.feedbackThanks}</p>
            ) : (
              <div
                className="feedback-rating"
                role="group"
                aria-label={strings.feedbackQuestion}
              >
                <p>{strings.feedbackQuestion}</p>
                <div className="feedback-stars">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      className="btn-secondary feedback-star"
                      aria-label={strings.feedbackStarLabel.replace("{n}", String(n))}
                      onClick={() => {
                        metrics.feedback(n);
                        setFeedbackGiven(true);
                      }}
                    >
                      {n}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {sessionId && screen.kind !== "ended" && (
        <footer className="kiosk-footer">
          <button className="btn-secondary" onClick={goBack}>
            ← {strings.back}
          </button>
          <div style={{ flex: 1 }} />
          <button className="btn-danger" onClick={() => setConfirmEndOpen(true)}>
            {strings.endSession}
          </button>
        </footer>
      )}

      {confirmEndOpen && (
        <div className="modal-overlay" role="alertdialog" aria-modal="true">
          <div className="modal">
            <h2>{strings.endSessionConfirmTitle}</h2>
            <p>{strings.endSessionConfirmBody}</p>
            <div className="modal-buttons">
              <button className="btn-primary" onClick={() => void endSession()}>
                {strings.endSessionConfirmYes}
              </button>
              <button className="btn-secondary" onClick={() => setConfirmEndOpen(false)}>
                {strings.endSessionConfirmNo}
              </button>
            </div>
          </div>
        </div>
      )}

      {inactivityWarn && !confirmEndOpen && (
        <div className="modal-overlay" role="alertdialog" aria-modal="true">
          <div className="modal">
            <h2>{strings.inactivityTitle}</h2>
            <p>{strings.inactivityBody}</p>
            <div className="modal-buttons">
              <button className="btn-primary btn-xl" onClick={() => void stayHere()}>
                {strings.inactivityStay}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

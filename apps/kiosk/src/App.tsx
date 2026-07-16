import { useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";
import type { Lang } from "./i18n";
import { t } from "./i18n";
import { HomeScreen } from "./screens/HomeScreen";
import { LanguageScreen } from "./screens/LanguageScreen";
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
  | { kind: "ended" };

export function App() {
  const [lang, setLang] = useState<Lang>("es");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [screen, setScreen] = useState<Screen>({ kind: "language" });
  const [fontScaleIdx, setFontScaleIdx] = useState(0);
  const [highContrast, setHighContrast] = useState(false);
  const [confirmEndOpen, setConfirmEndOpen] = useState(false);
  const [inactivityWarn, setInactivityWarn] = useState(false);
  const [error, setError] = useState(false);

  const warnTimer = useRef<number | undefined>(undefined);
  const endTimer = useRef<number | undefined>(undefined);
  const sessionRef = useRef<string | null>(null);
  sessionRef.current = sessionId;

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
    }, 4000);
  }, []);

  const endSession = useCallback(async () => {
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
    if (screen.kind === "procedure") setScreen({ kind: "home" });
    else if (screen.kind === "home") setConfirmEndOpen(true);
  };

  return (
    <div
      className={`kiosk${highContrast ? " high-contrast" : ""}`}
      style={{ ["--font-scale" as string]: FONT_SCALES[fontScaleIdx] }}
    >
      <header className="kiosk-header">
        <h1>{strings.appName}</h1>
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
        </div>
      </header>

      <main className="kiosk-main">
        {error && <div className="banner banner-info">{strings.apiError}</div>}

        {screen.kind === "language" && <LanguageScreen onChoose={(l) => void startSession(l)} />}

        {screen.kind === "home" && sessionId && (
          <HomeScreen
            lang={lang}
            onOpenProcedure={(procedureId) => setScreen({ kind: "procedure", procedureId })}
          />
        )}

        {screen.kind === "procedure" && sessionId && (
          <ProcedureScreen lang={lang} sessionId={sessionId} procedureId={screen.procedureId} />
        )}

        {screen.kind === "ended" && (
          <div className="centered-splash">
            <h2>{strings.sessionEndedTitle}</h2>
            <p>{strings.sessionEndedBody}</p>
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

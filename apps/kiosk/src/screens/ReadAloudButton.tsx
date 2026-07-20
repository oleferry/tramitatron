import { useEffect, useState } from "react";

import type { Lang } from "../i18n";
import { t } from "../i18n";
import { speak, speechSupported, stopSpeaking } from "../speech";

/**
 * Lectura en voz alta de un texto concreto (PRD §14.2).
 *
 * Volver a pulsar mientras lee la detiene; pulsar de nuevo la repite desde el
 * principio, que es el "repetición" del PRD sin añadir más controles. Si el
 * navegador no tiene síntesis de voz, el botón no se muestra en vez de
 * ofrecer algo que no funciona.
 */
export function ReadAloudButton({ text, lang }: { text: string; lang: Lang }) {
  const strings = t(lang);
  const [speaking, setSpeaking] = useState(false);

  // Al desmontar (cambio de pantalla) la voz debe callarse: si no, seguiría
  // leyendo la carta del usuario anterior.
  useEffect(() => stopSpeaking, []);

  if (!speechSupported() || !text.trim()) return null;

  const toggle = () => {
    if (speaking) {
      stopSpeaking();
      setSpeaking(false);
      return;
    }
    speak(text, lang);
    setSpeaking(true);
    // No hay evento fiable de fin en todos los navegadores: se vuelve al
    // estado inicial cuando la síntesis deja de estar activa.
    const poll = window.setInterval(() => {
      if (!window.speechSynthesis.speaking) {
        setSpeaking(false);
        window.clearInterval(poll);
      }
    }, 400);
  };

  return (
    <button className="btn-secondary btn-read-aloud" onClick={toggle} aria-pressed={speaking}>
      <span aria-hidden="true">{speaking ? "⏹️" : "🔊"}</span>{" "}
      {speaking ? strings.stopReading : strings.readAloud}
    </button>
  );
}

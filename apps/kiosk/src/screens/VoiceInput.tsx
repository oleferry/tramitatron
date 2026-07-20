import { useEffect, useRef, useState } from "react";

import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";

// Corte de seguridad: un turno de voz es corto (PRD §14.3, "textos breves").
// Evita además que una grabación olvidada siga capturando la sala.
const MAX_RECORDING_MS = 20_000;

type Phase = "idle" | "recording" | "transcribing" | "review" | "error";

/**
 * Pulsar para hablar (PRD §14.3).
 *
 * Cumple los requisitos del PRD punto por punto: se pulsa para empezar y para
 * parar (no hay que mantener pulsado, que es difícil con temblor o artritis),
 * hay indicador visible de grabación, la transcripción se muestra SIEMPRE
 * antes de usarse, hay que confirmarla, y hay botón para borrarla.
 *
 * El audio no sale del navegador salvo en la petición de transcripción, y ni
 * el audio ni el texto se guardan en el servidor.
 */
export function VoiceInput({
  lang,
  sessionId,
  onConfirmed,
}: {
  lang: Lang;
  sessionId: string;
  onConfirmed: (text: string) => void;
}) {
  const strings = t(lang);
  const [phase, setPhase] = useState<Phase>("idle");
  const [transcript, setTranscript] = useState("");
  const [usable, setUsable] = useState(true);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | undefined>(undefined);

  const releaseMicrophone = () => {
    recorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    recorderRef.current = null;
    window.clearTimeout(timerRef.current);
  };

  // Si el componente desaparece (cambio de pantalla, fin de sesión) el
  // micrófono debe soltarse sí o sí: nunca puede quedar grabando de fondo.
  useEffect(() => releaseMicrophone, []);

  const transcribe = async (blob: Blob) => {
    setPhase("transcribing");
    try {
      const base64 = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(",")[1]);
        reader.onerror = () => reject(new Error("read"));
        reader.readAsDataURL(blob);
      });
      const result = await api.transcribeAudio(sessionId, base64, blob.type || "audio/webm", lang);
      setTranscript(result.text);
      setUsable(result.usable);
      setPhase("review");
    } catch {
      setPhase("error");
    }
  };

  const start = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "audio/webm" });
        chunksRef.current = [];
        releaseMicrophone();
        void transcribe(blob);
      };
      recorderRef.current = recorder;
      recorder.start();
      setPhase("recording");
      timerRef.current = window.setTimeout(() => {
        if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      }, MAX_RECORDING_MS);
    } catch {
      setPhase("error");
    }
  };

  const stop = () => {
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
  };

  const discard = () => {
    setTranscript("");
    setPhase("idle");
  };

  return (
    <div className="voice-input">
      {phase === "idle" && (
        <button className="btn-voice" onClick={() => void start()}>
          <span aria-hidden="true">🎤</span> {strings.voiceStart}
        </button>
      )}

      {phase === "recording" && (
        <button className="btn-voice recording" onClick={stop} aria-live="polite">
          <span className="recording-dot" aria-hidden="true" /> {strings.voiceStop}
        </button>
      )}

      {phase === "transcribing" && (
        <p className="subtitle" aria-live="polite">
          {strings.voiceTranscribing}
        </p>
      )}

      {phase === "error" && (
        <div className="banner banner-info">
          {strings.voiceError}
          <button className="btn-secondary" onClick={discard}>
            {strings.voiceDiscard}
          </button>
        </div>
      )}

      {phase === "review" && (
        <div className="panel voice-review" aria-live="polite">
          <h3>
            <span aria-hidden="true">💬</span> {strings.voiceHeard}
          </h3>
          <p className="voice-transcript">“{transcript}”</p>
          {!usable && <p className="banner banner-info">{strings.voiceUnclear}</p>}
          <div className="voice-actions">
            {usable && (
              <button
                className="btn-primary"
                onClick={() => {
                  onConfirmed(transcript);
                  discard();
                }}
              >
                {strings.voiceConfirm}
              </button>
            )}
            <button className="btn-secondary" onClick={() => void start()}>
              {strings.voiceRetry}
            </button>
            <button className="btn-secondary" onClick={discard}>
              {strings.voiceDiscard}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";

import type { Lang } from "../i18n";
import { t } from "../i18n";

// Captura con la cámara del dispositivo (getUserMedia). El vídeo nunca sale
// del navegador: solo la foto que el usuario decide usar se envía a la API.
// Si no hay cámara o se deniega el permiso, el paso ofrece subir una foto.

// Restricciones de la cámara en UN solo sitio: cámara trasera y resolución alta
// para leer un documento. Se usan al arrancar y al reiniciar, sin duplicarlas.
const CAMERA_CONSTRAINTS: MediaStreamConstraints = {
  video: { facingMode: "environment", width: { ideal: 1600 } },
  audio: false,
};

export function CameraCapture({
  lang,
  onCaptured,
  onCancel,
}: {
  lang: Lang;
  onCaptured: (imageBase64: string, mimeType: "image/jpeg") => void;
  onCancel: () => void;
}) {
  const strings = t(lang);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [phase, setPhase] = useState<"starting" | "live" | "preview" | "error">("starting");
  const [photo, setPhoto] = useState<string | null>(null);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(CAMERA_CONSTRAINTS);
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setPhase("live");
      } catch {
        setPhase("error");
      }
    })();
    return () => {
      cancelled = true;
      stopStream();
    };
  }, [stopStream]);

  const takePhoto = () => {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")!.drawImage(video, 0, 0);
    setPhoto(canvas.toDataURL("image/jpeg", 0.85));
    setPhase("preview");
    stopStream();
  };

  const restart = () => {
    setPhoto(null);
    setPhase("starting");
    // Reinicia el efecto volviendo a montar el stream.
    (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia(CAMERA_CONSTRAINTS);
        streamRef.current = stream;
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
        }
        setPhase("live");
      } catch {
        setPhase("error");
      }
    })();
  };

  const usePhoto = () => {
    if (!photo) return;
    onCaptured(photo.split(",")[1], "image/jpeg");
  };

  if (phase === "error") {
    return (
      <div className="doc-step">
        <div className="banner banner-info">{strings.cameraError}</div>
        <button className="btn-secondary" onClick={onCancel}>
          {strings.cancelCapture}
        </button>
      </div>
    );
  }

  return (
    <div className="doc-step">
      <p className="subtitle">{strings.captureFrameHint}</p>
      <div className="camera-box">
        {phase !== "preview" && (
          // eslint-disable-next-line jsx-a11y/media-has-caption
          <video ref={videoRef} playsInline muted />
        )}
        {phase === "preview" && photo && <img src={photo} alt={strings.scanTitle} />}
        <div className="camera-frame" aria-hidden="true" />
      </div>
      {phase === "starting" && (
        <p className="subtitle" role="status">
          {strings.cameraStarting}
        </p>
      )}
      <div className="doc-step-buttons">
        {phase === "live" && (
          <button className="btn-primary btn-xl" onClick={takePhoto}>
            📷 {strings.takePhoto}
          </button>
        )}
        {phase === "preview" && (
          <>
            <button className="btn-primary" onClick={usePhoto}>
              {strings.usePhoto}
            </button>
            <button className="btn-secondary" onClick={restart}>
              {strings.retakePhoto}
            </button>
          </>
        )}
        <button className="btn-secondary" onClick={onCancel}>
          {strings.cancelCapture}
        </button>
      </div>
    </div>
  );
}

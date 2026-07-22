import { useRef, useState } from "react";

import type { DocumentClass, DocumentExtraction, ExtractedField } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { CameraCapture } from "./CameraCapture";

// Paso documental de un trámite: consentir → capturar (cámara o foto subida)
// → revisar/corregir → confirmar. Los valores solo viven en la sesión efímera;
// el usuario siempre los ve antes de que se usen (PRD §11.4).
export function DocumentStep({
  lang,
  sessionId,
  documentClass,
  onConfirmed,
}: {
  lang: Lang;
  sessionId: string;
  documentClass: DocumentClass;
  onConfirmed: () => void;
}) {
  const strings = t(lang);
  const [phase, setPhase] = useState<"idle" | "capture" | "scanning" | "review" | "done">(
    "idle",
  );
  const [extraction, setExtraction] = useState<DocumentExtraction | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [fieldStatus, setFieldStatus] = useState<Record<string, ExtractedField["status"]>>({});
  const [failed, setFailed] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const upload = async (imageBase64: string, mimeType: "image/png" | "image/jpeg") => {
    setPhase("scanning");
    setFailed(false);
    try {
      const result = await api.uploadDocument(sessionId, documentClass, imageBase64, mimeType);
      setExtraction(result);
      setValues(Object.fromEntries(result.fields.map((f) => [f.field, f.value])));
      setFieldStatus(Object.fromEntries(result.fields.map((f) => [f.field, f.status])));
      setPhase("review");
    } catch {
      setFailed(true);
      setPhase("idle");
    }
  };

  const onFileChosen = (file: File | undefined) => {
    if (!file) return;
    const mimeType = file.type === "image/png" ? "image/png" : "image/jpeg";
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      void upload(dataUrl.split(",")[1], mimeType);
    };
    reader.readAsDataURL(file);
  };

  const confirm = async () => {
    if (!extraction) return;
    setFailed(false);
    try {
      const result = await api.confirmDocument(sessionId, extraction.document_id, values);
      setFieldStatus(Object.fromEntries(result.fields.map((f) => [f.field, f.status])));
      if (result.accepted) {
        setPhase("done");
        onConfirmed();
      }
    } catch {
      setFailed(true);
    }
  };

  if (phase === "done") {
    return <div className="banner banner-success">✅ {strings.dataConfirmed}</div>;
  }

  return (
    <div className="panel">
      <h3>
        <span aria-hidden="true">🪪</span> {strings.scanTitle}
      </h3>

      {failed && <div className="banner banner-info">{strings.apiError}</div>}

      {phase === "idle" && (
        <div className="doc-step">
          <p className="subtitle">{strings.scanIntro}</p>
          {/* El botón es el consentimiento explícito para usar la cámara (TT-202). */}
          <button className="btn-primary" onClick={() => setPhase("capture")}>
            📷 {strings.scanButton}
          </button>
          <button
            className="btn-secondary"
            onClick={() => fileInputRef.current?.click()}
          >
            {strings.uploadPhoto}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png"
            style={{ display: "none" }}
            onChange={(e) => onFileChosen(e.target.files?.[0])}
          />
        </div>
      )}

      {phase === "capture" && (
        <CameraCapture
          lang={lang}
          onCaptured={(imageBase64, mimeType) => void upload(imageBase64, mimeType)}
          onCancel={() => setPhase("idle")}
        />
      )}

      {phase === "scanning" && (
        <p className="subtitle" role="status">
          {strings.scanning}
        </p>
      )}

      {phase === "review" && extraction && (
        <div className="doc-step">
          <p className="subtitle">
            <strong>{strings.reviewTitle}.</strong> {strings.reviewIntro}
          </p>
          {extraction.fields.map((f) => {
            const status = fieldStatus[f.field];
            const hasHint = status === "REVIEW_REQUIRED" || status === "INVALID";
            const hintId = `dochint-${f.field}`;
            return (
              <label key={f.field} className="field-row">
                <span className="field-label">{strings.fieldLabels[f.field] ?? f.field}</span>
                <input
                  value={values[f.field] ?? ""}
                  onChange={(e) => setValues({ ...values, [f.field]: e.target.value })}
                  className={
                    status === "INVALID"
                      ? "field-invalid"
                      : status === "REVIEW_REQUIRED"
                        ? "field-review"
                        : ""
                  }
                  // El lector de pantalla anuncia el estado del campo y por qué;
                  // no basta con el color (WCAG 3.3.1/4.1.2).
                  aria-invalid={status === "INVALID"}
                  aria-describedby={hasHint ? hintId : undefined}
                  // Tótem COMPARTIDO: sin autocompletar ni guardar datos sensibles
                  // en el navegador; nada del anterior debe reaparecer.
                  autoComplete="off"
                  autoCapitalize="off"
                  spellCheck={false}
                />
                {status === "REVIEW_REQUIRED" && (
                  <span id={hintId} className="field-hint field-hint-review">
                    ⚠️ {strings.fieldReview}
                  </span>
                )}
                {status === "INVALID" && (
                  <span id={hintId} className="field-hint field-hint-invalid">
                    ✖ {strings.fieldInvalid}
                  </span>
                )}
              </label>
            );
          })}
          <div className="doc-step-buttons">
            <button className="btn-primary" onClick={() => void confirm()}>
              {strings.confirmData}
            </button>
            <button className="btn-secondary" onClick={() => setPhase("idle")}>
              {strings.rescan}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

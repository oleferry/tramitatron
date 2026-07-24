import { useEffect, useState } from "react";

import type { DocumentClass } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { PrivacyNotice } from "./PrivacyNotice";
import { ReadAloudButton } from "./ReadAloudButton";

/**
 * Consentimiento informado antes de leer un documento (art. 13 y consentimiento
 * explícito del art. 6.1.a / 9.2.a, EIPD §3.2). Cumple lo que exige la EIPD:
 * dice qué se hará, que la imagen no se guarda, y ofrece SIEMPRE la alternativa
 * humana. El texto se adapta a la postura del despliegue (`documents_to_ai`):
 * solo menciona el servicio automatizado cuando de verdad está activo, para no
 * afirmar nada falso.
 *
 * El "Sí, doy mi permiso" es el consentimiento; "No, prefiero una persona" es la
 * alternativa equivalente, que nunca se penaliza.
 */
export function DocumentConsent({
  lang,
  documentClass,
  voiceEnabled,
  onConsent,
  onDecline,
}: {
  lang: Lang;
  documentClass: DocumentClass;
  voiceEnabled: boolean;
  onConsent: () => void;
  onDecline: () => void;
}) {
  const strings = t(lang);
  const [documentsToAi, setDocumentsToAi] = useState(false);
  const [showNotice, setShowNotice] = useState(false);

  // Postura de datos del despliegue. Si no se puede consultar, se asume lo más
  // prudente (sin IA): no se afirma un tratamiento que quizá no ocurre.
  useEffect(() => {
    let alive = true;
    api
      .getVersion()
      .then((v) => alive && setDocumentsToAi(v.documents_to_ai))
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);

  const documentName = strings.documentNames[documentClass] ?? documentClass;
  const lines = [
    strings.consentIntro.replace("{document}", documentName),
    strings.consentNoStore,
    documentsToAi ? strings.consentAiProcessing : "",
    strings.consentHumanAlt,
  ].filter(Boolean);

  return (
    <div className="panel consent">
      <h3>🔒 {strings.consentTitle}</h3>
      {lines.map((line, i) => (
        <p key={i} className="consent-line">
          {line}
        </p>
      ))}

      {voiceEnabled && (
        <ReadAloudButton lang={lang} text={[strings.consentTitle, ...lines].join(". ")} />
      )}

      <div className="consent-actions">
        <button className="btn-primary btn-xl" onClick={onConsent}>
          ✅ {strings.consentAllow}
        </button>
        <button className="btn-secondary" onClick={onDecline}>
          {strings.consentDecline}
        </button>
        <button className="btn-link" onClick={() => setShowNotice(true)}>
          {strings.consentMore}
        </button>
      </div>

      {showNotice && (
        <PrivacyNotice
          lang={lang}
          documentsToAi={documentsToAi}
          voiceEnabled={voiceEnabled}
          onClose={() => setShowNotice(false)}
        />
      )}
    </div>
  );
}

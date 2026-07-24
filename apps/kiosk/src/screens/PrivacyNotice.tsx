import { Modal } from "../Modal";
import { CONTROLLER_NAME, PRIVACY_CONTACT } from "../deployment";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { ReadAloudButton } from "./ReadAloudButton";

/**
 * Aviso de privacidad (información del art. 13 RGPD) en lenguaje claro y
 * bilingüe. Se muestra a demanda, antes de que la persona entregue ningún dato,
 * desde la pantalla de consentimiento. El responsable del tratamiento y el
 * contacto son propios de cada despliegue (deployment.ts).
 *
 * `documentsToAi` adapta el texto para no afirmar nada falso: solo se menciona
 * el servicio automatizado de lectura cuando el despliegue lo tiene activo.
 */
export function PrivacyNotice({
  lang,
  documentsToAi,
  voiceEnabled,
  onClose,
}: {
  lang: Lang;
  documentsToAi: boolean;
  voiceEnabled: boolean;
  onClose: () => void;
}) {
  const strings = t(lang);

  const lines = [
    strings.privacyResponsible.replace("{controller}", CONTROLLER_NAME),
    strings.privacyPurpose,
    strings.privacyBasis,
    strings.privacyNoAccount,
    strings.privacyRecipients,
    documentsToAi ? strings.privacyAi : "",
    strings.privacyNoAutoDecision,
    strings.privacyRights.replace("{contact}", PRIVACY_CONTACT),
  ].filter(Boolean);

  return (
    <Modal titleId="privacy-title" bodyId="privacy-body" onEscape={onClose}>
      <h2 id="privacy-title">🔒 {strings.privacyTitle}</h2>
      <div id="privacy-body" className="privacy-body">
        {lines.map((line, i) => (
          <p key={i}>{line}</p>
        ))}
      </div>
      {voiceEnabled && <ReadAloudButton lang={lang} text={[strings.privacyTitle, ...lines].join(". ")} />}
      <div className="modal-buttons">
        <button className="btn-primary" onClick={onClose}>
          {strings.privacyClose}
        </button>
      </div>
    </Modal>
  );
}

import { useState } from "react";

import type { IntakeField } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";

/**
 * Recogida de datos NO sensibles antes de preparar el trámite (servicio,
 * oficina, fecha…), para que el worker los precomplete. Una pregunta por
 * pantalla (PRD §14.2: una decisión por paso). Al terminar, guarda todo en la
 * sesión y avisa al padre para ejecutar.
 *
 * Aquí no se piden datos personales sensibles (DNI, tarjeta sanitaria): esos
 * vienen del escaneo del documento, con su revisión y confirmación.
 */
export function IntakeStep({
  lang,
  sessionId,
  fields,
  onComplete,
}: {
  lang: Lang;
  sessionId: string;
  fields: IntakeField[];
  onComplete: () => void;
}) {
  const strings = t(lang);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);

  const field = fields[idx];

  const answer = async (value: string) => {
    const next = { ...answers, [field.key]: value };
    setAnswers(next);
    setText("");
    if (idx + 1 < fields.length) {
      setIdx(idx + 1);
      return;
    }
    // Última pregunta: guarda todo en la sesión y cede el paso al padre.
    setSaving(true);
    await Promise.all(
      Object.entries(next).map(([key, val]) =>
        api.setSessionData(sessionId, key, val).catch(() => undefined),
      ),
    );
    onComplete();
  };

  const progress = strings.intakeProgress
    .replace("{n}", String(idx + 1))
    .replace("{total}", String(fields.length));

  return (
    <div className="panel intake">
      <p className="intake-progress">{progress}</p>
      <h3>{field.label[lang]}</h3>

      {field.type === "select" ? (
        <div className="intake-options">
          {field.options.map((opt) => (
            <button
              key={opt.value}
              className="btn-secondary btn-xl"
              disabled={saving}
              onClick={() => void answer(opt.value)}
            >
              {opt.label[lang]}
            </button>
          ))}
        </div>
      ) : (
        <form
          className="intake-text"
          onSubmit={(e) => {
            e.preventDefault();
            if (text.trim()) void answer(text.trim());
          }}
        >
          <input
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            aria-label={field.label[lang]}
          />
          <button className="btn-primary btn-xl" type="submit" disabled={!text.trim() || saving}>
            {strings.intakeNext}
          </button>
        </form>
      )}
    </div>
  );
}

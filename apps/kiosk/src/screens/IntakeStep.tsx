import { useEffect, useRef, useState } from "react";

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
  // Devuelve lo elegido para que la pantalla pueda enseñar el resumen de la
  // cita antes de reservarla ("Esta es tu cita, ¿la confirmo?").
  onComplete: (answers: Record<string, string>) => void;
}) {
  const strings = t(lang);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const headingRef = useRef<HTMLHeadingElement>(null);

  const field = fields[idx];

  // Al avanzar de paso, lleva el foco al encabezado de la nueva pregunta para
  // que el lector de pantalla la lea. El paso 0 no se enfoca aquí: al montar,
  // App.tsx ya mueve el foco a <main> y leerlo dos veces sería redundante.
  useEffect(() => {
    if (idx > 0) headingRef.current?.focus({ preventScroll: true });
  }, [idx]);

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
    onComplete(next);
  };

  const progress = strings.intakeProgress
    .replace("{n}", String(idx + 1))
    .replace("{total}", String(fields.length));

  return (
    <div className="panel intake">
      <p className="intake-progress">{progress}</p>
      {/* tabIndex=-1: enfocable por código (para anunciar la pregunta al cambiar
          de paso) pero fuera del recorrido normal del tabulador. */}
      <h3 ref={headingRef} tabIndex={-1}>
        {field.label[lang]}
      </h3>

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

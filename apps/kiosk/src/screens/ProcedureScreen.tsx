import { useEffect, useRef, useState } from "react";

import type { ExecutionResult, Procedure } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { procedureIcon } from "../icons";
import { AskPanel } from "./AskPanel";
import { DocumentStep } from "./DocumentStep";
import { IntakeStep } from "./IntakeStep";
import { QrCode } from "./QrCode";
import { ReadAloudButton } from "./ReadAloudButton";

export function ProcedureScreen({
  lang,
  sessionId,
  procedureId,
  voiceEnabled,
}: {
  lang: Lang;
  sessionId: string;
  procedureId: string;
  voiceEnabled: boolean;
}) {
  const strings = t(lang);
  const [procedure, setProcedure] = useState<Procedure | null>(null);
  const [result, setResult] = useState<ExecutionResult | null>(null);
  const [printed, setPrinted] = useState(false);
  const [handoffPrinted, setHandoffPrinted] = useState(false);
  const [failed, setFailed] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [documentConfirmed, setDocumentConfirmed] = useState(false);
  const [intakeDone, setIntakeDone] = useState(false);
  // Lo que la persona ha elegido en el intake, para enseñárselo en el resumen
  // antes de reservar. Solo datos NO sensibles (centro, día, hora).
  const [intakeAnswers, setIntakeAnswers] = useState<Record<string, string>>({});
  // Cerrojo SÍNCRONO: el estado de React se actualiza de forma diferida, así que
  // dos toques en el mismo ciclo verían ambos executing=false. El ref se lee y
  // escribe al instante y sí bloquea la segunda ejecución.
  const executingRef = useRef(false);

  useEffect(() => {
    api
      .getProcedure(procedureId)
      .then(setProcedure)
      .catch(() => setFailed(true));
  }, [procedureId]);

  if (failed) return <div className="banner banner-info">{strings.apiError}</div>;
  if (!procedure) return <p className="subtitle">{strings.loading}</p>;

  const execute = async () => {
    // Guarda contra doble ejecución: el conector del worker recorre un portal
    // de varias páginas y tarda; sin esto, un segundo toque lanzaría otra
    // ejecución (otra incidencia y otra métrica) sobre la misma sesión. El ref
    // corta ya en el mismo tick; el estado solo pinta el "Preparando…".
    if (executingRef.current) return;
    executingRef.current = true;
    setExecuting(true);
    try {
      setResult(await api.executeProcedure(procedureId, sessionId));
    } catch {
      setFailed(true);
    } finally {
      executingRef.current = false;
      setExecuting(false);
    }
  };

  const print = async () => {
    if (!result?.receipt) return;
    try {
      await api.printReceipt([
        strings.appName,
        procedure.name[lang],
        `${strings.receiptReference}: ${result.receipt.reference}`,
        result.receipt.timestamp,
      ]);
      setPrinted(true);
    } catch {
      // La impresora simulada puede no estar arrancada; no es un error de sesión.
      setPrinted(false);
      setFailed(true);
    }
  };

  // Respaldo en papel de la cesión (TT-502): quien no lleve móvil se lleva el
  // enlace oficial y los pasos pendientes para terminarlo en casa. Nunca se
  // imprimen datos personales: la URL solo lleva las selecciones del trámite.
  const printHandoff = async () => {
    if (!result?.receipt) return;
    const pending = (result.receipt.pending ?? "")
      .split(", ")
      .filter(Boolean)
      .map((step) => `- ${strings.pendingLabels[step] ?? step}`);
    try {
      await api.printReceipt([
        strings.appName,
        procedure.name[lang],
        strings.handoffContinue,
        result.receipt.url ?? "",
        "",
        strings.handoffPending,
        ...pending,
      ]);
      setHandoffPrinted(true);
    } catch {
      setHandoffPrinted(false);
    }
  };

  return (
    <div className="screen">
      <div className="language-hero" aria-hidden="true">
        {procedureIcon(procedure.id)}
      </div>
      <h2>{procedure.name[lang]}</h2>
      {procedure.description && <p className="subtitle">{procedure.description[lang]}</p>}

      {procedure.status === "coming_soon" && (
        <div className="banner banner-info">
          {strings.comingSoonBanner} {strings.comingSoonHelp}
        </div>
      )}

      {procedure.requirements.length > 0 && (
        <div className="panel">
          <h3>
            <span aria-hidden="true">📋</span> {strings.requirementsTitle}
          </h3>
          <ul>
            {procedure.requirements.map((req, i) => (
              <li key={i}>{req[lang]}</li>
            ))}
          </ul>
          {voiceEnabled && (
            <ReadAloudButton
              lang={lang}
              text={[
                procedure.name[lang],
                strings.requirementsTitle,
                ...procedure.requirements.map((req) => req[lang]),
              ].join(". ")}
            />
          )}
        </div>
      )}

      {procedure.official_sources.length > 0 && (
        <div className="panel">
          <h3>
            <span aria-hidden="true">🔗</span> {strings.officialSourcesTitle}
          </h3>
          <ul>
            {procedure.official_sources.map((src) => (
              <li key={src}>{src}</li>
            ))}
          </ul>
        </div>
      )}

      <AskPanel lang={lang} procedureId={procedureId} />

      {procedure.execution_mode === "assisted" && (
        <p className="subtitle">{strings.assistedModeNote}</p>
      )}

      {procedure.execution_mode === "information" && (
        <p className="subtitle">{strings.informationModeNote}</p>
      )}

      {(() => {
        const intake = procedure.intake ?? [];
        const runnable = procedure.status === "available" && procedure.execution_mode !== "information";
        if (!runnable || result) return null;

        // 1) Datos NO sensibles (servicio, oficina, fecha…) para el prefill.
        if (intake.length > 0 && !intakeDone) {
          return (
            <IntakeStep
              lang={lang}
              sessionId={sessionId}
              fields={intake}
              onComplete={(answers) => {
                setIntakeAnswers(answers);
                setIntakeDone(true);
              }}
            />
          );
        }
        // 2) Documento (DNI/SIP) con revisión y confirmación, si hace falta.
        if (procedure.required_fields.length > 0 && !documentConfirmed) {
          return (
            <DocumentStep
              lang={lang}
              sessionId={sessionId}
              documentClass={
                procedure.required_fields.includes("sip_number") ? "sip_card" : "dni"
              }
              onConfirmed={() => setDocumentConfirmed(true)}
            />
          );
        }
        // 3) Todo recogido: lanzar el conector. Mientras prepara (el worker
        // puede tardar) el botón se sustituye por un estado anunciable, de modo
        // que no se puede volver a pulsar y el lector de pantalla oye el avance.
        if (executing) {
          return (
            <p className="subtitle" role="status">
              ⏳ {strings.executing}
            </p>
          );
        }
        // 3) Resumen antes de reservar: la persona ve su cita en cristiano y la
        // confirma. Ese "sí" es lo que autoriza al sistema a reservar; sin él
        // no se envía nada (el servidor lo exige igual).
        if (intake.length > 0) {
          return (
            <div className="panel booking-review">
              <h3>{strings.reviewBookingTitle}</h3>
              <dl className="booking-summary">
                {intake.map((f) => {
                  const chosen = intakeAnswers[f.key];
                  const label =
                    f.options.find((o) => o.value === chosen)?.label[lang] ?? chosen;
                  return (
                    <div key={f.key} className="booking-row">
                      <dt>{f.label[lang]}</dt>
                      <dd>{label}</dd>
                    </div>
                  );
                })}
              </dl>
              <button className="btn-primary btn-xl" onClick={() => void execute()}>
                ✅ {strings.confirmBooking}
              </button>
            </div>
          );
        }
        return (
          <button className="btn-primary btn-xl" onClick={() => void execute()}>
            {strings.confirmAndRun}
          </button>
        );
      })()}

      {result?.status === "completed" && result.receipt && (
        <div className="banner banner-success">
          <p style={{ margin: 0 }}>{strings.executionDone}</p>
          <p style={{ margin: 0 }}>
            {strings.receiptReference}: {result.receipt.reference}
          </p>
          {!printed ? (
            <button className="btn-secondary" onClick={() => void print()}>
              {strings.printReceipt}
            </button>
          ) : (
            <p style={{ margin: 0 }}>{strings.printed}</p>
          )}
        </div>
      )}

      {/* Navegación asistida: el sistema ha preparado el trámite y cede a la
          persona. Se muestra la URL oficial y los pasos que le quedan. */}
      {result?.status === "user_handoff" && result.receipt && (
        <div className="banner banner-info handoff">
          <p>
            <strong>{strings.handoffTitle}</strong>
          </p>
          {result.receipt.url && (
            <div className="handoff-qr">
              <QrCode value={result.receipt.url} label={strings.qrLabel} />
              <div className="handoff-qr-text">
                <p>
                  <strong>{strings.qrTitle}</strong>
                </p>
                <p>{strings.qrInstruction}</p>
                <p className="handoff-url">
                  {strings.handoffContinue} <span>{result.receipt.url}</span>
                </p>
                <p className="handoff-privacy">🔒 {strings.qrNoData}</p>
              </div>
            </div>
          )}
          {result.receipt.pending && (
            <>
              <p>{strings.handoffPending}</p>
              <ul>
                {result.receipt.pending.split(", ").map((step) => (
                  <li key={step}>{strings.pendingLabels[step] ?? step}</li>
                ))}
              </ul>
            </>
          )}
          {result.receipt.url && (
            <div className="handoff-print">
              <p className="subtitle">{strings.handoffNoPhone}</p>
              {!handoffPrinted ? (
                <button className="btn-secondary" onClick={() => void printHandoff()}>
                  🖨️ {strings.printHandoff}
                </button>
              ) : (
                <p style={{ margin: 0 }}>{strings.printed}</p>
              )}
            </div>
          )}
          {voiceEnabled && (
            <ReadAloudButton
              lang={lang}
              text={[
                strings.handoffTitle,
                result.receipt.url ? strings.qrInstruction : "",
                strings.handoffPending,
                ...(result.receipt.pending ?? "")
                  .split(", ")
                  .map((step) => strings.pendingLabels[step] ?? step),
              ]
                .filter(Boolean)
                .join(". ")}
            />
          )}
        </div>
      )}

      {result?.status === "failed" && (
        <div className="banner banner-info">
          {result.message ?? strings.handoffFailed}
          {result.incident_code && (
            <div className="incident-code">
              {strings.incidentCode}: <strong>{result.incident_code}</strong>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

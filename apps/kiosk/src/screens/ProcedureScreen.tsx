import { useEffect, useState } from "react";

import type { ExecutionResult, Procedure } from "../api";
import { api } from "../api";
import type { Lang } from "../i18n";
import { t } from "../i18n";
import { procedureIcon } from "../icons";
import { AskPanel } from "./AskPanel";
import { DocumentStep } from "./DocumentStep";
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
  const [failed, setFailed] = useState(false);
  const [documentConfirmed, setDocumentConfirmed] = useState(false);

  useEffect(() => {
    api
      .getProcedure(procedureId)
      .then(setProcedure)
      .catch(() => setFailed(true));
  }, [procedureId]);

  if (failed) return <div className="banner banner-info">{strings.apiError}</div>;
  if (!procedure) return <p className="subtitle">{strings.loading}</p>;

  const execute = async () => {
    try {
      setResult(await api.executeProcedure(procedureId, sessionId));
    } catch {
      setFailed(true);
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

      {procedure.status === "available" &&
        procedure.execution_mode !== "information" &&
        procedure.required_fields.length > 0 &&
        !result && (
        <DocumentStep
          lang={lang}
          sessionId={sessionId}
          documentClass={procedure.required_fields.includes("sip_number") ? "sip_card" : "dni"}
          onConfirmed={() => setDocumentConfirmed(true)}
        />
      )}

      {procedure.status === "available" &&
        procedure.execution_mode !== "information" &&
        !result &&
        (procedure.required_fields.length === 0 || documentConfirmed) && (
          <button className="btn-primary btn-xl" onClick={() => void execute()}>
            {strings.confirmAndRun}
          </button>
        )}

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
            <p className="handoff-url">
              {strings.handoffContinue} <span>{result.receipt.url}</span>
            </p>
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
          {voiceEnabled && (
            <ReadAloudButton
              lang={lang}
              text={[
                strings.handoffTitle,
                strings.handoffPending,
                ...(result.receipt.pending ?? "")
                  .split(", ")
                  .map((step) => strings.pendingLabels[step] ?? step),
              ].join(". ")}
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

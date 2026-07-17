# ADR-003 — RAG extractivo sobre fuentes oficiales versionadas

**Estado:** aceptada
**Fecha:** 2026-07-17
**Contexto:** PRD §16 (conocimiento oficial y RAG), TT-303, regla 7 del §30
(la IA no puede invocar URLs arbitrarias)

## Decisión

1. **Allowlist declarativa** en `knowledge/sources.yaml`: id, URL, organismo,
   título, territorio, trámites asociados y cadencia de revisión. Solo estas
   URLs pueden ingerirse.

2. **Ingesta con hash y versionado por git** (`python -m app.knowledge.ingest`):
   descarga cada fuente, extrae el texto (parser propio de la stdlib, sin
   dependencias nuevas; filtra líneas de navegación y aprovecha las
   metaetiquetas oficiales en webs SPA), calcula SHA-256 y solo escribe un
   snapshot nuevo si el contenido cambió. `snapshots/index.json` apunta al
   snapshot vigente; el historial de versiones es el historial de git.
   Una fuente que falla queda en estado `error` y el asistente deja de
   usarla automáticamente (despublicación, PRD §16.2).

3. **Respuesta extractiva, no generativa.** El recuperador puntúa fragmentos
   por solape léxico normalizado (ponderación por rareza de término, peso de
   «densidad de prosa» contra los menús, preferencia ×3 por las fuentes del
   trámite en contexto) y devuelve un **extracto literal** del snapshot con
   organismo, título, fecha de consulta y enlace. Sin fragmento relevante,
   la respuesta es «no encontrado» y derivación. Con esto es estructuralmente
   imposible alucinar requisitos: el sistema solo puede citar.

4. **El gateway sigue siendo la vía de mejora.** Cuando haya proveedor de IA,
   `explain_official_content` recibirá los fragmentos recuperados y redactará
   una explicación en lenguaje claro citando la fuente; la recuperación y la
   allowlist no cambian.

## Consecuencias

- El asistente ya responde con contenido oficial real (GVA, SITVAL,
  Diputación de Castellón) y muestra siempre fuente y fecha.
- Calidad conocida y asumida: las webs institucionales son ricas en menús;
  el extracto puede incluir items de navegación. Mejorará con (a) resumen
  por modelo vía gateway y (b) ingesta con Playwright para webs SPA como
  SITVAL (hoy solo aportan sus metadescripciones oficiales).
- La ingesta es manual/CI por ahora; la programación por cadencia
  (`review_cadence`) y la alerta por cambio de hash se conectarán al panel
  de operación en la fase 4.

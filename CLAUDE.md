# CLAUDE.md — Tramitatrón

## Fuente única de verdad

Lee `docs/TRAMITATRON_MASTER_PRD.md` antes de diseñar o implementar nada. Este fichero solo resume las reglas operativas; el PRD manda.

## Reglas obligatorias (PRD §30)

1. No reutilices código de `/legacy` salvo pequeñas funciones cubiertas primero con tests.
2. No añadas funcionalidades fuera del MVP (alcance en PRD §5).
3. El sistema es anónimo por defecto: sin cuentas, sin memoria entre sesiones.
4. No guardes PII ni documentos en logs, base de datos o almacenamiento persistente (clasificación de datos en PRD §13.2).
5. No automatices CAPTCHAs, firma, Cl@ve o credenciales.
6. Toda acción externa requiere schemas tipados y confirmación del usuario.
7. La IA no puede invocar URLs arbitrarias; solo fuentes del catálogo.
8. Monolito modular + worker Playwright separado. Nada de microservicios en el MVP.
9. Castellano y valenciano (i18n) desde el primer componente.
10. Tests y documentación en cada entrega.
11. Sin acoplamiento a un proveedor de IA: todo pasa por el model gateway (PRD §10).
12. Prioriza una demo local reproducible con Docker Compose.

## Estructura de repositorio objetivo

La estructura de monorepo está definida en PRD §9.3 (`apps/`, `services/`, `packages/`, `connectors/`, `knowledge/`, `infra/`, `docs/`, `tests/`, `legacy/`).

## Estado y próximo hito (PRD §32)

Hito 1 ✅, **fase 2 completa** (servicio documental efímero, RAG extractivo, cartas TT-404, voz) y **fase 3 iniciada**: worker de navegación asistida (`services/browser-worker`, TT-502/505) con Playwright, verificado en local. Catálogo de 14 trámites (los de conector automático en `coming_soon`, los informativos activos). Siguiente: conectar el worker al kiosco (pantalla de handoff) y, tras la EIPD, un portal real.

Reglas prácticas aprendidas:
- La API carga catálogo y conocimiento **al arrancar**; tras editar YAMLs de `connectors/catalog/` o reingerir `knowledge/`, reinicia la API (`--reload` solo vigila `.py`).
- Para añadir un trámite: YAML en `connectors/catalog/` + icono en `apps/kiosk/src/icons.ts` (prefijos específicos antes) + regla de intención en `app/gateway/mock.py` + fuente en `knowledge/sources.yaml` + `python -m app.knowledge.ingest` + tests.
- La extracción de documentos, el OCR de cartas y la transcripción de voz son sintéticos (mock): ignoran la imagen y el audio. No prometer lectura real de DNI, OCR ni reconocimiento de voz hasta conectar proveedores.
- Voz (`app/voice/`): **no persiste nada**, ni audio ni transcripción (PRD §13.2 y E2E-01). No añadir ahí `set_data`. La transcripción se muestra y requiere confirmación; con confianza < 0,60 se oculta el botón de confirmar. La síntesis de voz es local del navegador a propósito (ADR-005), no pasa por el gateway.
- En cartas (`app/letters/`), la IA **solo transcribe**: riesgo, plazos y datos sensibles son reglas deterministas (ADR-004). No mover esa lógica a un modelo. Ante la duda, el análisis escala el riesgo, nunca lo baja.
- De los datos sensibles se informa del **tipo** ("contiene tu DNI"), jamás del valor. Hay tests que lo fijan.
- Si tocas `demo.ts`, recuerda que replica el backend para la preview de Vercel: al añadir un endpoint o un trámite hay que actualizarlo también.
- Worker de navegación (`services/browser-worker/`): servicio SEPARADO (regla 8). **Prepara y cede**: nunca reserva ni automatiza CAPTCHA/Cl@ve (regla 5); su resultado terminal es siempre `user_handoff`. Allowlist estricta de hosts (regla 7). Driver simulado (httpx, por defecto y en tests) y Playwright (extra opcional). Portales reales (GVA, SITVAL) declarados pero `enabled=False` hasta EIPD (ADR-007). El driver de Playwright no está en el extra `dev` (CI no lo instala): los tests usan el simulado.
- El worker está conectado al kiosco: `WorkerConnector` (`app/connectors/worker.py`) llama al worker vía `BROWSER_WORKER_URL`; el trámite `demo.worker.appointment` (catálogo, `execution_mode: integrated`) lo dispara. Sin worker configurado, `execute` devuelve `failed` con mensaje, no rompe. El kiosco renderiza `user_handoff` (URL oficial + pasos pendientes) en `ProcedureScreen`. Si tocas `demo.worker`, actualiza también `demo.ts`.
- Gateway de IA (`app/gateway/`): `AnthropicModelGateway` es real pero **el mock es el valor por defecto** y el fallback permanente (regla 12). Sin `ANTHROPIC_API_KEY` no sale nada de la máquina. Los datos A2 (imágenes de DNI/SIP, cartas) van detrás de `ANTHROPIC_ALLOW_DOCUMENTS` (apagado; requiere EIPD, PRD §10.4 y §13.2, ADR-006). La voz nunca usa Claude (no hace STT). El gateway no registra valores de PII. El camino con llamadas reales a Claude no está probado en local (sin clave).

No trabajar en conectores reales (GVA Salud, SITVAL) hasta que las pruebas de privacidad de fase 2 estén completas.

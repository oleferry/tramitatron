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

Hito 1 ✅, **fase 2 completa** (servicio documental efímero, RAG extractivo, cartas TT-404, voz), **fase 3 iniciada** (worker de navegación asistida `services/browser-worker`, TT-502/505, con Playwright, verificado en local y conectado al kiosco) y **fase 4 iniciada**: panel institucional de KPIs (TT-602, `services/api/app/metrics/` + `apps/admin/`, agregados anónimos), verificado en local. Catálogo de 15 trámites adaptado a Castilla y León (conectores automáticos en `coming_soon`, informativos activos). Siguiente: tras la EIPD, un portal real; y el resto de EPIC 6 (registro de tótems, incidencias, versión).

Reglas prácticas aprendidas:
- Idiomas por despliegue: la i18n es bilingüe (regla 9) y no se toca, pero los idiomas ACTIVOS se limitan con `VITE_LOCALES` (`apps/kiosk/src/locales.ts`). Con un solo idioma, el kiosco omite la pantalla de selección y arranca en ese idioma. El piloto actual (Castilla y León, sin lengua cooficial) va con `VITE_LOCALES=es` (en `vercel.json`); que falte el selector NO es un bug. Reactivar el valenciano = `VITE_LOCALES=es,ca-valencia`. La CI de accesibilidad usa el build por defecto (bilingüe), así que sus tests del selector siguen aplicando.
- Accesibilidad (TT-701, EPIC 7): `apps/kiosk/tests/a11y.spec.ts` corre axe-core (Playwright) sobre la app real y exige WCAG 2.2 AA (PRD §14.5). Cualquier cambio de UI o de la paleta debe mantener `npm run test:a11y` en verde, en tema normal y alto contraste. Necesita `npx playwright install chromium`; hay job de CI `a11y`.
- La API carga catálogo y conocimiento **al arrancar**; tras editar YAMLs de `connectors/catalog/` o reingerir `knowledge/`, reinicia la API (`--reload` solo vigila `.py`).
- Para añadir un trámite: YAML en `connectors/catalog/` + icono en `apps/kiosk/src/icons.ts` (prefijos específicos antes) + regla de intención en `app/gateway/mock.py` + fuente en `knowledge/sources.yaml` + `python -m app.knowledge.ingest` + tests.
- La extracción de documentos, el OCR de cartas y la transcripción de voz son sintéticos (mock): ignoran la imagen y el audio. No prometer lectura real de DNI, OCR ni reconocimiento de voz hasta conectar proveedores.
- Voz (`app/voice/`): **no persiste nada**, ni audio ni transcripción (PRD §13.2 y E2E-01). No añadir ahí `set_data`. La transcripción se muestra y requiere confirmación; con confianza < 0,60 se oculta el botón de confirmar. La síntesis de voz es local del navegador a propósito (ADR-005), no pasa por el gateway.
- En cartas (`app/letters/`), la IA **solo transcribe**: riesgo, plazos y datos sensibles son reglas deterministas (ADR-004). No mover esa lógica a un modelo. Ante la duda, el análisis escala el riesgo, nunca lo baja.
- De los datos sensibles se informa del **tipo** ("contiene tu DNI"), jamás del valor. Hay tests que lo fijan.
- Si tocas `demo.ts`, recuerda que replica el backend para la preview de Vercel: al añadir un endpoint o un trámite hay que actualizarlo también.
- Worker de navegación (`services/browser-worker/`): servicio SEPARADO (regla 8). **Prepara y cede**: nunca reserva ni automatiza CAPTCHA/Cl@ve (regla 5); su resultado terminal es siempre `user_handoff`. Allowlist estricta de hosts (regla 7). Driver simulado (httpx, por defecto y en tests) y Playwright (extra opcional). Portales reales (GVA, SITVAL) declarados pero `enabled=False` hasta EIPD (ADR-007). El driver de Playwright no está en el extra `dev` (CI no lo instala): los tests usan el simulado.
- El worker está conectado al kiosco: `WorkerConnector` (`app/connectors/worker.py`) llama al worker vía `BROWSER_WORKER_URL`; el trámite `demo.worker.appointment` (catálogo, `execution_mode: integrated`) lo dispara. Sin worker configurado, `execute` devuelve `failed` con mensaje, no rompe. El kiosco renderiza `user_handoff` (URL oficial + pasos pendientes) en `ProcedureScreen`. Si tocas `demo.worker`, actualiza también `demo.ts`.
- Panel de KPIs (`app/metrics/`, TT-602): SOLO contadores agregados en memoria (se reinician con la API). Nunca id de sesión, texto, imagen ni audio; ninguna métrica prohibida (PRD §18.2). Hay tests que fijan la ausencia de PII en `/summary` y en el CSV. La instrumentación autoritativa la hace el SERVIDOR en sus routers (sesión → idioma/franja; ejecución → completado/derivación/fallo; asistente/cartas/voz/documentos → uso por canal). El kiosco solo emite señales de UI (`started`/`abandoned`/`feedback`) vía el cliente `metrics` de `api.ts`, a fuego y olvido (no activan el modo demo ni pasan por `demo.ts`). Lectura del panel protegible con `ADMIN_TOKEN` (si se define, `/summary` y `/summary.csv` exigen `Authorization: Bearer`); la ingesta del kiosco es siempre pública (anónima). El panel `apps/admin/index.html` es estático, se sirve en `/admin` (Vercel) y necesita que `CORS_ORIGINS` incluya su origen para hablar con la API.
- Gateway de IA (`app/gateway/`): `AnthropicModelGateway` es real pero **el mock es el valor por defecto** y el fallback permanente (regla 12). Sin `ANTHROPIC_API_KEY` no sale nada de la máquina. Los datos A2 (imágenes de DNI/SIP, cartas) van detrás de `ANTHROPIC_ALLOW_DOCUMENTS` (apagado; requiere EIPD, PRD §10.4 y §13.2, ADR-006). La voz nunca usa Claude (no hace STT). El gateway no registra valores de PII. El camino con llamadas reales a Claude no está probado en local (sin clave).

No trabajar en conectores reales (GVA Salud, SITVAL) hasta que las pruebas de privacidad de fase 2 estén completas.

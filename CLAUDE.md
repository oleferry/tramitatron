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

Hito 1 ✅ completado. Fase 2 en curso: servicio documental efímero, RAG extractivo y explicación de cartas (TT-404) funcionan; catálogo ampliado a 14 trámites (los de conector automático en `coming_soon`, los informativos activos). Pendiente de fase 2: voz. Después, conectores reales con Playwright (fase 3, TT-502..505).

Reglas prácticas aprendidas:
- La API carga catálogo y conocimiento **al arrancar**; tras editar YAMLs de `connectors/catalog/` o reingerir `knowledge/`, reinicia la API (`--reload` solo vigila `.py`).
- Para añadir un trámite: YAML en `connectors/catalog/` + icono en `apps/kiosk/src/icons.ts` (prefijos específicos antes) + regla de intención en `app/gateway/mock.py` + fuente en `knowledge/sources.yaml` + `python -m app.knowledge.ingest` + tests.
- La extracción de documentos y la transcripción de cartas son sintéticas (mock): ignoran la imagen. No prometer lectura real de DNI ni OCR hasta implementar un `ModelGateway` de visión.
- En cartas (`app/letters/`), la IA **solo transcribe**: riesgo, plazos y datos sensibles son reglas deterministas (ADR-004). No mover esa lógica a un modelo. Ante la duda, el análisis escala el riesgo, nunca lo baja.
- De los datos sensibles se informa del **tipo** ("contiene tu DNI"), jamás del valor. Hay tests que lo fijan.
- Si tocas `demo.ts`, recuerda que replica el backend para la preview de Vercel: al añadir un endpoint o un trámite hay que actualizarlo también.

No trabajar en conectores reales (GVA Salud, SITVAL) hasta que las pruebas de privacidad de fase 2 estén completas.

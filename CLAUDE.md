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

## Próximo hito (PRD §32)

Hito 1 — repositorio ejecutable y núcleo anónimo: monorepo, Docker local, frontend kiosco con pantalla de idioma, API FastAPI con `/health`, sesión efímera con purga, catálogo mock, gateway IA mock, simulador de periféricos, pruebas de aislamiento, ADR-001.

No trabajar en conectores reales (GVA Salud, SITVAL) hasta completar el hito 1 y las pruebas de privacidad.

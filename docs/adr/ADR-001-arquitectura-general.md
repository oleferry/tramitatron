# ADR-001 — Arquitectura general del hito 1

**Estado:** aceptada
**Fecha:** 2026-07-16
**Contexto:** PRD §9 (arquitectura técnica) y §32 (hito 1)

## Decisión

1. **Monorepo modular** con `apps/` (frontends), `services/` (backend y agentes), `connectors/` (catálogo declarativo y futuros conectores), `docs/` y `legacy/` (referencia, prohibido importar).

2. **Monolito modular en FastAPI** (`services/api`), no microservicios. Módulos internos con contratos claros: `sessions`, `catalog`, `gateway`, `connectors`. La única separación de proceso prevista es el worker de Playwright (fase 3), porque un navegador automatizado no puede compartir proceso con la API (problema documentado del prototipo heredado).

3. **Sesiones efímeras detrás de un protocolo `SessionStore`** con dos implementaciones: memoria (desarrollo/tests) y Redis con TTL nativo (despliegue). Ninguna implementación escribe en disco. El TTL por defecto es 20 minutos (PRD §13.1) y la purga es idempotente y demostrable por test.

4. **Catálogo declarativo en YAML** (`connectors/catalog/*.yaml`) validado con Pydantic en el arranque. Un YAML inválido impide arrancar: es preferible a mostrar un trámite mal definido. Los campos siguen el esquema del PRD §12.1 (`execution_mode`, `risk_class`, `captcha_policy: user_only`, `document_retention: none`).

5. **Gateway multimodelo como protocolo** (`ModelGateway`): la lógica de negocio no conoce proveedores de IA. El hito 1 incluye solo `MockModelGateway` (clasificación determinista por palabras clave), suficiente para desarrollar y probar el kiosco. La selección de proveedor real es una decisión de fase 0/1 pendiente (PRD §25.5) y no bloquea nada.

6. **Frontend del kiosco con React + TypeScript + Vite** (PWA con manifest, modo fullscreen). Se elige Vite frente a Next.js porque el kiosco no necesita SSR ni routing de servidor: es una SPA de pantalla completa con estados locales. Menos superficie, arranque más rápido en hardware modesto.

7. **Device-agent separado** (`services/device-agent`), hoy en modo simulador (impresora → ficheros de spool, cámara → imagen sintética). En el tótem real escuchará solo en localhost y hablará con hardware.

8. **Observabilidad sin vigilancia desde el día 1**: el middleware de acceso registra método, ruta y estado — nunca query strings ni cuerpos. La suite `test_privacy.py` verifica con centinelas que ningún dato personal aparece en logs ni en respuestas de listado.

## Consecuencias

- Se puede desarrollar todo el flujo del kiosco sin proveedor de IA, sin hardware y sin tocar portales externos.
- Cambiar el mock por un proveedor real (o Redis por otro almacén) no toca la lógica de negocio.
- PostgreSQL está en el compose pero sin uso hasta la fase 4 (métricas/catálogo versionado): decisión consciente para no diseñar esquema antes de necesitarlo.
- La imagen Docker del kiosco es de desarrollo (servidor Vite); la imagen de producción con build estático y modo kiosco llega en fase 5.

# Tramitatrón

Punto público de asistencia digital para trámites administrativos, instalado en tótems físicos en sedes institucionales (ayuntamientos, centros sociales, oficinas comarcales). Permite a cualquier persona —especialmente mayores o con baja competencia digital— entender, preparar y completar trámites con ayuda de IA multimodal (texto, voz y documentos).

**Ámbito inicial:** provincia de Castellón, micro-piloto en 1–3 municipios.

## Documento maestro

Toda la especificación de producto, arquitectura, seguridad, privacidad y roadmap está en:

📄 [`docs/TRAMITATRON_MASTER_PRD.md`](docs/TRAMITATRON_MASTER_PRD.md)

Ese documento es la **fuente única de verdad** del proyecto. Léelo íntegramente antes de contribuir.

## Principios innegociables

- **Anónimo por defecto**: sin cuentas de ciudadano, sin PII persistente, purga al cerrar sesión.
- **La IA guía y prepara; no decide ni envía sin confirmación** del usuario.
- **No se automatizan CAPTCHAs, firma, Cl@ve ni credenciales.**
- **API antes que navegador; navegador antes que promesas falsas.**
- **Accesibilidad integral** (WCAG 2.2 AA, EN 301 549) y bilingüe castellano/valenciano desde el primer componente.

## Estado

🚧 **Fase 0 — Descubrimiento y cimentación.** El repositorio se está arrancando desde cero como reescritura controlada del prototipo heredado (Universidad de Vigo), que se archivará en `/legacy` solo como referencia.

## Stack previsto

- **Frontend kiosco:** Next.js/React + TypeScript, PWA en modo kiosco.
- **Backend:** Python 3.12+, FastAPI, PostgreSQL, Redis.
- **Automatización asistida:** Playwright en worker separado.
- **Infra local:** Docker Compose.

## Cómo empezar (desarrollo)

```bash
git clone https://github.com/oleferry/tramitatron.git
cd tramitatron
# La estructura de monorepo y el docker-compose llegarán con el hito 1 (ver PRD §32)
```

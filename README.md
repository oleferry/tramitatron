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

✅ **Hito 1 completado** (PRD §32): API con sesiones efímeras, catálogo declarativo, gateway IA mock, conector mock, kiosco bilingüe con purga de datos, simulador de periféricos, pruebas de aislamiento/privacidad y CI.

✅ **Fase 2 en curso**: servicio documental efímero (extracción con validadores deterministas DNI/NIE/SIP y revisión obligatoria del usuario) y RAG extractivo sobre fuentes oficiales versionadas (`knowledge/`), con organismo, fecha y enlace en cada respuesta.

🚧 Siguiente: explicación de cartas administrativas (TT-404) y voz; después, conectores reales con Playwright (fase 3).

## Estructura

```text
apps/kiosk/            Interfaz del tótem (React + TypeScript + Vite, PWA)
services/api/          API FastAPI: sesiones, catálogo, gateway IA, conectores
services/device-agent/ Agente de periféricos (hito 1: modo simulador)
connectors/catalog/    Catálogo declarativo de trámites (YAML validado)
knowledge/             Fuentes oficiales (allowlist) y snapshots versionados
docs/adr/              Decisiones de arquitectura
```

## Cómo ejecutarlo

### Opción A — Docker (entorno completo)

```bash
cp .env.example .env   # y edita POSTGRES_PASSWORD
docker compose up --build
```

### Opción B — Nativo (sin Docker)

En tres terminales:

```bash
# 1. API (http://localhost:8000/docs)
cd services/api
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"   # Linux/mac: .venv/bin/pip
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# 2. Simulador de periféricos
cd services/device-agent
python -m venv .venv && .venv/Scripts/pip install -e ".[dev]"
.venv/Scripts/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8210

# 3. Kiosco (http://localhost:5173)
cd apps/kiosk
npm install
npm run dev
```

Sin Redis configurado, la API usa un almacén de sesiones en memoria (solo desarrollo). Con `REDIS_URL` definido, usa Redis con TTL nativo.

### Despliegue

- **Kiosco (web)**: Vercel, importando este repo tal cual (`vercel.json` define el build). Sin backend accesible, el kiosco pasa automáticamente a modo demostración con distintivo visible.
- **API (región UE)**: Render mediante blueprint (`render.yaml`): servicio Docker + Redis gestionado, ambos en **Frankfurt**. En render.com → *New → Blueprint* → seleccionar este repositorio. La imagen es `infra/docker/api.Dockerfile` (incluye catálogo y snapshots de conocimiento). Cada push a `master` redespliega.

### Tests

```bash
cd services/api && .venv/Scripts/python -m pytest -q          # 27 tests
cd services/device-agent && .venv/Scripts/python -m pytest -q # 3 tests
cd apps/kiosk && npm run build                                # typecheck + build
```

La suite incluye pruebas de **aislamiento entre sesiones** (E2E-05 del PRD) y de **privacidad**: valores centinela de PII no pueden aparecer en logs ni en respuestas de listado.

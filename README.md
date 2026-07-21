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

✅ **Catálogo ampliado**: 14 trámites declarados — DNI, Hacienda (AEAT), Seguridad Social (INSS y vida laboral), SEPE, DGT, extranjería, tarjeta SIP, empadronamiento (Castelló) y certificados del Ministerio de Justicia — con fuente oficial ingerida para el asistente. Los que requieren conector automático quedan `coming_soon` (PRD §5.4: DNI/SS/AEAT no deben ser los primeros conectores por CAPTCHA y autenticación); los informativos (`execution_mode: information`) están activos y explican cómo hacer el trámite citando la fuente oficial.

✅ **Explicación de cartas (TT-404)**: el ciudadano fotografía una carta administrativa y el kiosco le separa **lo que pone el documento** de **lo que entiende el sistema**. El modelo solo transcribe; el riesgo, los plazos y los datos sensibles se deciden con reglas deterministas auditables ([ADR-004](docs/adr/ADR-004-explicacion-de-cartas.md)), de modo que una alucinación no pueda rebajar la gravedad de un embargo. Ante términos de riesgo o plazos ambiguos, deriva a atención humana y nunca sugiere una actuación jurídica concreta.

✅ **Voz**: pulsar para hablar con indicador de grabación, transcripción visible y confirmación obligatoria antes de usarla, botón de borrar y desactivación desde la cabecera. Ni el audio ni la transcripción se guardan en ningún sitio ([ADR-005](docs/adr/ADR-005-canal-de-voz.md)). La lectura en voz alta usa la síntesis local del navegador, para no enviar el contenido de las cartas a un proveedor externo.

✅ **Proveedor de IA real (opcional)**: el gateway (PRD §10) tiene ya una implementación sobre Claude además del mock. **Seguro por defecto**: sin `ANTHROPIC_API_KEY` funciona con el mock y no sale ningún dato de la máquina. Con clave, la clasificación de intención usa Claude; el envío de imágenes de DNI/SIP y cartas (datos A2) va detrás de un segundo interruptor **apagado por defecto** porque requiere EIPD ([ADR-006](docs/adr/ADR-006-proveedor-ia-real.md)). La voz nunca usa Claude (no hace STT de audio).

✅ **Fase 3 — worker de navegación asistida (Playwright)**: servicio separado (`services/browser-worker`) que **prepara y cede** (TT-502): navega el portal de la allowlist, precompleta los campos seguros y **se detiene** en el CAPTCHA, la identificación y la confirmación, que hace la persona. Nunca reserva ni automatiza CAPTCHA/Cl@ve (regla 5). Dos drivers: simulado (httpx contra un portal de pruebas local, por defecto y en tests) y Playwright real (Chromium, extra opcional, verificado en local). Healthchecks sintéticos que no reservan (TT-505). Los portales reales (GVA, SITVAL) están declarados pero **desactivados** hasta completar privacidad/EIPD ([ADR-007](docs/adr/ADR-007-worker-navegacion-asistida.md)).

🚧 Siguiente: conectar el worker al kiosco (pantalla de handoff) y, tras la EIPD, un portal real.

## Estructura

```text
apps/kiosk/            Interfaz del tótem (React + TypeScript + Vite, PWA)
services/api/          API FastAPI: sesiones, catálogo, gateway IA, conectores
services/device-agent/ Agente de periféricos (hito 1: modo simulador)
services/browser-worker/ Worker de navegación asistida (Playwright): prepara y cede
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
cd services/api && .venv/Scripts/python -m pytest -q          # 103 tests
cd services/device-agent && .venv/Scripts/python -m pytest -q # 3 tests
cd services/browser-worker && .venv/Scripts/python -m pytest -q # 10 tests
cd apps/kiosk && npm run build                                # typecheck + build
```

La suite incluye pruebas de **aislamiento entre sesiones** (E2E-05 del PRD) y de **privacidad**: valores centinela de PII no pueden aparecer en logs ni en respuestas de listado.

### Probar con una webcam

La captura de documentos usa la cámara del navegador (`getUserMedia`), que funciona en `localhost` sin HTTPS. Con los tres servicios arrancados:

1. Abre el kiosco, elige idioma y entra en **Trámite de demostración** (el único `available` con captura).
2. Pulsa el botón de capturar documento → el navegador pedirá permiso de cámara.
3. Encuadra el documento, captura, revisa y confirma.

**Importante:** la extracción actual es **sintética** (`MockModelGateway.extract_document` ignora la imagen y devuelve siempre `PERSONA SINTÉTICA DEMO`, DNI `12345678Z`). Sirve para probar cámara, encuadre, revisión y purga — no para leer documentos reales. La lectura real llegará al implementar un `ModelGateway` con proveedor de visión (`services/api/app/gateway/base.py`). Si no hay cámara, el flujo ofrece subir una foto como alternativa.

### Actualizar el conocimiento del asistente

```bash
cd services/api && .venv/Scripts/python -m app.knowledge.ingest
```

Descarga las fuentes de `knowledge/sources.yaml` (allowlist), y solo escribe snapshot nuevo si el contenido cambió. El asistente responde siempre con extractos literales de estas fuentes, nunca texto inventado. **La API carga catálogo y conocimiento al arrancar: tras editar YAMLs o reingerir, reiníciala.**

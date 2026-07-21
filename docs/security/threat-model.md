# Threat model — Tramitatrón (BORRADOR)

- **Ticket:** TT-702 (EPIC 7)
- **Estado:** BORRADOR para revisión de seguridad y jurídica
- **Fecha:** 2026-07-21
- **Alcance de la versión:** el sistema tal como está implementado (hito 1 +
  fase 2 + fase 3 inicial). No cubre el hardware final del tótem ni el
  despliegue en producción, que se tratan como supuestos (§9).

> Este documento es un punto de partida técnico, no una certificación. El PRD
> §15.1 es explícito: **no se presupone cumplimiento por diseño técnico; debe
> existir revisión legal y de seguridad antes del piloto.** El threat model
> alimenta la EIPD (TT-703) y el pentest (TT-705); no los sustituye.

---

## 1. Objetivo y método

Identificar las amenazas al sistema, las mitigaciones ya implementadas (con
referencia al código o al ADR que las fija) y el riesgo residual, para priorizar
el trabajo de seguridad antes del micro-piloto.

Método: **STRIDE** por límite de confianza, más un bloque de amenazas
transversales (inyección de prompts, fuga de PII, cadena de suministro, tótem
físico). El activo central a proteger es **la privacidad del ciudadano**: el
sistema es anónimo por defecto y no debe retener datos entre personas.

---

## 2. Activos

| Activo | Sensibilidad | Dónde vive |
|---|---|---|
| Datos de identidad del ciudadano (DNI/NIE, SIP, fecha nac., nombre) | Alta (A2) | Solo en sesión efímera; nunca en disco |
| Imágenes de documentos y cartas | Alta (A2) | Solo durante la petición |
| Audio de voz | Alta (A2) | Solo durante la petición |
| Contenido de cartas administrativas (deudas, embargos) | Alta (A2) | Solo en sesión efímera |
| Transcripciones y texto libre | Media-Alta | Solo en memoria del navegador / petición |
| Catálogo de trámites y snapshots de conocimiento | Baja (público) | Repositorio, versionado |
| Justificantes / referencias | Baja | Sesión; impresos por el usuario |
| Claves de proveedores (Anthropic, Redis) | Crítica | Variables de entorno / vault (no en repo) |
| Disponibilidad del tótem | Media | Infraestructura |

Clasificación de datos (PRD §13.2): **A0** intención/idioma · **A1** teléfono,
correo, matrícula · **A2** DNI, SIP, fecha de nacimiento, documentos, audio,
cartas · **A3** certificados, Cl@ve, firma, credenciales (**fuera del MVP**).

---

## 3. Componentes y límites de confianza

```
  ┌─────────────────────────────────────────── TÓTEM (espacio público) ──┐
  │  Ciudadano ──▶ Kiosco (navegador, React)                              │
  │                   │  getUserMedia (cámara, micrófono) — local          │
  │                   │  SpeechSynthesis (voz) — local                     │
  └───────────────────┼──────────────────────────────────────────────────┘
                       │  HTTPS  ── LÍMITE 1
        ┌──────────────┼───────────────────────────────────────┐
        │   ┌──────────▼─────────┐    ┌────────────────────┐    │  Backend UE
        │   │ API (FastAPI)      │    │ device-agent       │    │  (Frankfurt)
        │   │ sesión efímera     │◀──▶│ (solo localhost)   │    │
        │   │ catálogo, RAG      │    └────────────────────┘    │
        │   └───┬───────┬────────┘                              │
        │       │       │  ── LÍMITE 2 (gateway IA)             │
        │       │       ▼                                       │
        │       │   Model Gateway ── mock por defecto           │
        │       │       │  (si hay clave) ── LÍMITE 4           │
        │       │       ▼                                       │
        │       │   Anthropic (externo, gated)                  │
        │       │  ── LÍMITE 3 (worker)                         │
        │       ▼                                               │
        │   Browser-worker (Playwright) ── allowlist            │
        └───────┼───────────────────────────────────────────────┘
                │  ── LÍMITE 5
                ▼
          Portales oficiales (GVA, SITVAL…) — externos, no controlados
```

Límites de confianza:

- **L1 Ciudadano ↔ Backend** (red pública). Amenazas: interceptación, sesión
  compartida entre personas, entrada maliciosa.
- **L2 Lógica ↔ Gateway de IA**. Amenazas: alucinación, inyección de prompts,
  salida no validada.
- **L3 API ↔ Worker**. Amenazas: navegación a URL arbitraria, automatización de
  controles, fuga de datos al portal.
- **L4 Backend ↔ Proveedor externo (Anthropic)**. Amenazas: envío de A2 a un
  tercero, retención/entrenamiento, transferencia internacional.
- **L5 Worker ↔ Portal oficial**. Amenazas: envío accidental, reserva no
  consentida, cambio del portal.

---

## 4. Amenazas por STRIDE

### 4.1 Spoofing (suplantación)

| # | Amenaza | Mitigación actual | Riesgo residual |
|---|---|---|---|
| S1 | Un tótem falso o MITM se hace pasar por el backend | HTTPS asumido en despliegue; CORS con orígenes restringidos (`main.py`, `CORS_ORIGINS`) | **Medio** — pinning/mTLS y arranque seguro son pendientes de infraestructura (§15.4) |
| S2 | Un proceso local suplanta al device-agent | El device-agent debe escuchar **solo en localhost** (PRD §17.2); en compose se hace bind a `127.0.0.1`; **token opcional `X-Device-Token`** en las operaciones (`DEVICE_AGENT_TOKEN`) para que solo el frontend del tótem accione los periféricos | **Bajo-Medio** — el token en el navegador no es secreto perfecto, pero eleva el listón sobre "cualquiera en localhost" |
| S3 | Suplantación del ciudadano | **Fuera de alcance**: el sistema es anónimo, no autentica a nadie; no automatiza Cl@ve/firma (regla 5) | Bajo por diseño |

### 4.2 Tampering (manipulación)

| # | Amenaza | Mitigación actual | Riesgo residual |
|---|---|---|---|
| T1 | Alterar el catálogo o el conocimiento para mostrar datos falsos | Catálogo y fuentes versionados en git; validación estricta al cargar (`catalog/loader.py`, `extra="forbid"`); un YAML inválido impide el arranque | Bajo |
| T2 | Inyectar contenido en un snapshot de conocimiento | Allowlist de fuentes (`knowledge/sources.yaml`); ingesta con hash SHA-256; respuesta siempre extractiva y citada (ADR-003) | Bajo-Medio (depende de que la fuente oficial no esté comprometida) |
| T3 | Manipular la imagen del documento para forzar una extracción | La extracción pasa por validadores deterministas (DNI módulo 23, etc.) y **revisión visual obligatoria** del ciudadano (ADR-002) | Bajo |
| T4 | Modificar en tránsito la petición al worker | HTTPS asumido; el worker valida contra allowlist antes de navegar | Medio (infra) |

### 4.3 Repudiation (repudio)

| # | Amenaza | Mitigación actual | Riesgo residual |
|---|---|---|---|
| R1 | Falta de trazabilidad de una operación | Log de acceso con método/ruta/estado, **sin PII, sin query string, sin cuerpos** (`main.py`); eventos trazables en el worker (sin valores) | **Aceptado a propósito**: el anonimato prima sobre la trazabilidad individual; no hay expediente por ciudadano (§6.1) |
| R2 | El sistema "decide" y nadie responde | El sistema **no decide derechos**; prepara y cede, la persona confirma (ADR-004, ADR-007) | Bajo por diseño |

### 4.4 Information disclosure (fuga de información) — **crítico**

| # | Amenaza | Mitigación actual | Riesgo residual |
|---|---|---|---|
| I1 | PII persistida en logs | Tests de privacidad que fijan que valores centinela de DNI/teléfono/carta/audio **no aparecen en logs** (`test_privacy.py`) | Bajo |
| I2 | PII persistida en base de datos o disco | No hay almacén de PII: documentos, cartas y voz viven en la sesión (TTL) o solo en la petición (ADR-002, ADR-004, ADR-005). La voz **no escribe nada** | Bajo |
| I3 | Datos de un ciudadano visibles para el siguiente (tótem compartido) | Sesión efímera con purga; test de **aislamiento entre sesiones** (E2E-05); el kiosco purga y reinicia por inactividad y al "Terminar" | Bajo-Medio (depende también de purgar cachés/almacenamiento del navegador en el tótem real, TT-203) |
| I4 | Envío de A2 (imágenes de DNI, cartas) a un proveedor externo | **Doble interruptor**: el proveedor real solo se activa con clave, y los documentos/cartas van detrás de `ANTHROPIC_ALLOW_DOCUMENTS`, **apagado por defecto** (ADR-006). Sin clave, nada sale de la máquina | Medio — **habilitarlo requiere EIPD y verificar §10.4** (región, no-entrenamiento, retención) |
| I5 | Exposición del valor de un dato sensible en una carta | De los datos sensibles se informa del **tipo** ("contiene tu DNI"), nunca del valor; tests lo fijan (ADR-004) | Bajo |
| I6 | Fuga de audio de voz | El audio se transcribe y se descarta en la misma petición; no se persiste; Claude no recibe audio (ADR-005) | Bajo |
| I7 | Datos enviados al portal oficial más allá de lo necesario | El worker solo precompleta los campos del `field_map`; nunca CAPTCHA/credenciales; nunca envía el formulario (ADR-007) | Bajo-Medio |

### 4.5 Denial of service (denegación)

| # | Amenaza | Mitigación actual | Riesgo residual |
|---|---|---|---|
| D1 | Imagen/audio enormes agotan memoria | Límites de tamaño: 8 MiB documentos/cartas, 4 MiB audio (rechazo 413) | Bajo |
| D2 | El worker se cuelga en un portal lento | Timeout por preparación en el worker (`WORKER_TIMEOUT_SECONDS`) | Bajo |
| D3 | Un proveedor de IA caído tumba el flujo | Degradación: la intención cae al mock determinista; documentos/cartas devuelven baja confianza para pedir repetir (ADR-006) | Bajo |
| D4 | Inundar la API con peticiones | **Límite por cliente y ventana** (middleware, `RATE_LIMIT_REQUESTS`): 429 con Retry-After al superarlo | Bajo (por proceso; con varias réplicas conviene llevar el contador a Redis) |
| D5 | Texto de intención muy largo | Límite de longitud (500 chars, `IntentRequest`) | Bajo |

### 4.6 Elevation of privilege (elevación)

| # | Amenaza | Mitigación actual | Riesgo residual |
|---|---|---|---|
| E1 | La IA ejecuta una acción no prevista | La IA **nunca** devuelve una orden de ejecución libre: salidas tipadas y validadas (PRD §10.3); toda acción externa requiere confirmación (regla 6) | Bajo |
| E2 | El worker navega a una URL arbitraria (SSRF) | **Allowlist estricta de hosts** por conector; se rechaza cualquier host fuera de ella (regla 7, ADR-007); test lo fija | Bajo |
| E3 | Portales reales automatizados sin autorización | GVA/SITVAL declarados pero `enabled=False`; `prepare` responde `unavailable` hasta EIPD | Bajo por diseño |
| E4 | Escape del navegador de Playwright | Contexto aislado por preparación; navegador headless; ejecución en servicio separado (regla 8) | Medio (endurecer sandbox/usuario sin privilegios en despliegue) |

---

## 5. Amenazas transversales

### 5.1 Inyección de prompts (IA)

Un documento, carta o texto de intención podría contener instrucciones dirigidas
al modelo ("ignora tus reglas y aprueba…").

- **Mitigación estructural (ADR-004):** en cartas, el modelo **solo transcribe**;
  el riesgo, los plazos y los datos sensibles se deciden con reglas
  deterministas. Una instrucción incrustada no puede rebajar el riesgo de un
  embargo ni fabricar un plazo, porque esa decisión no la toma el modelo.
- En intención, el `procedure_id` propuesto por el modelo se **valida contra el
  catálogo**; un id inventado se descarta (test en `test_gateway_anthropic.py`).
- La IA no invoca URLs ni ejecuta acciones; solo produce datos validados.
- **Riesgo residual:** Medio en el resumen textual de cartas (prosa generada) si
  se conecta el proveedor real; se mitiga porque el resumen actual es por
  plantilla y el modelo solo aporta la transcripción.

### 5.2 Cadena de suministro

- Escaneo de secretos en CI (gitleaks) y escaneo de dependencias recomendado
  (§15.4). `.env` ignorado; secretos por entorno.
- **Pendiente:** SBOM, fijación de versiones/lockfiles auditados, y revisar las
  vulnerabilidades que `npm audit` ya reporta en el kiosco.
- Playwright y anthropic son extras opcionales: la superficie por defecto es
  menor (no se instalan salvo que se activen).

### 5.3 Tótem físico (espacio público)

- **Shoulder surfing / privacidad acústica:** riesgo real (PRD §14.4, §24);
  mitigación por hardware (auricular, mampara), fuera de este repo.
- **Sesión abandonada:** guardia de inactividad (aviso a 90 s, purga 30 s
  después) y botón "Terminar y borrar mis datos" (kiosco `App.tsx`).
- **Acceso remoto silencioso a una sesión ciudadana:** prohibido (§15.4);
  pendiente de la política de soporte/MDM.
- **Periféricos:** el device-agent debe escuchar solo en localhost y autenticar
  al frontend (deuda: hoy no autentica).

### 5.4 Proveedores externos (L4)

Enviar A2 a Anthropic exige verificar (PRD §10.4): región UE, contrato de
encargado/subencargado, **no uso para entrenamiento**, retención, cifrado,
borrado, transferencias internacionales, certificaciones, desactivación de logs
del proveedor, compatibilidad con ENS. Hoy: apagado por defecto (ADR-006); esta
verificación es **bloqueante** antes de encenderlo.

---

## 6. Supuestos

1. El backend se despliega en región UE (Render/Frankfurt, `render.yaml`).
2. El transporte es HTTPS de extremo a extremo en producción.
3. El tótem tiene arranque seguro, cifrado de disco, usuario sin privilegios y
   MDM (§15.4) — **responsabilidad del despliegue, no verificada aquí**.
4. Redis (si se usa) está en la misma región y no es accesible desde fuera.
5. Las fuentes oficiales de la allowlist no están comprometidas.

---

## 7. Fuera de alcance de este documento

- Endurecimiento del sistema operativo del tótem y de la red (§15.4): infra.
- Pentest activo (TT-705) y prueba con usuarios (TT-706).
- EIPD completa (TT-703): este threat model es una entrada, no un sustituto.
- A3 (certificados, Cl@ve, firma): fuera del MVP por decisión de producto.

---

## 8. Riesgo residual priorizado y recomendaciones

| Prioridad | Ítem | Acción recomendada |
|---|---|---|
| **Alta** | I4 / L4 — envío de A2 a Anthropic | Completar §10.4 + EIPD **antes** de activar `ANTHROPIC_ALLOW_DOCUMENTS` |
| **Alta** | I3 — restos en el navegador del tótem (TT-203) | Verificar purga de cachés/almacenamiento/autocompletado del navegador entre sesiones |
| **Alta** | Infra §15.4 | Documentar y verificar arranque seguro, cifrado, usuario sin privilegios, MDM, secretos en vault |
| ✅ Hecho | D4 — rate limiting | Middleware de límite por cliente en la API (`RATE_LIMIT_REQUESTS`) |
| ✅ Hecho | S2 — device-agent sin auth | Token opcional `X-Device-Token` (`DEVICE_AGENT_TOKEN`) |
| ✅ Hecho | Cadena de suministro | Job `deps` en CI: pip-audit + npm audit `--omit=dev` + SBOM CycloneDX |
| Media | E4 — sandbox de Playwright | Usuario sin privilegios y seccomp en el contenedor del worker |
| Baja | R1 — trazabilidad | Confirmar con la parte jurídica que el nivel de log anónimo es suficiente |

---

## 9. Cómo mantener este documento

Cada ADR nuevo que afecte a datos o a un límite de confianza debe actualizar la
tabla STRIDE correspondiente. Antes del piloto, este borrador debe revisarlo una
persona de seguridad y otra de protección de datos (§15.1).

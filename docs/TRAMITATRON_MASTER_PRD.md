# TRAMITATRÓN — Documento maestro de producto y desarrollo

**Versión:** 0.1  
**Fecha:** 16 de julio de 2026  
**Estado:** Base de desarrollo para Claude Code  
**Propietario funcional:** Semilla Empresarial S.L.  
**Ámbito inicial:** provincia de Castellón, con micro-piloto en 1–3 municipios  
**Canal principal:** tótem físico institucional  
**Canales posteriores:** web móvil, atención telefónica y otros canales reutilizando el mismo backend  

---

## 0. Propósito de este documento

Este documento es la **fuente única de verdad** para reconstruir Tramitatrón desde cero aprovechando:

1. La idea, posicionamiento y modelo de servicio ya definidos.
2. El prototipo desarrollado con la Universidad de Vigo.
3. El conocimiento obtenido al automatizar trámites reales.
4. Las capacidades actuales de modelos de inteligencia artificial multimodales.
5. Un diseño compatible con contratación pública, accesibilidad, privacidad y operación institucional.

No es un dossier comercial. Es simultáneamente:

- PRD — *Product Requirements Document*.
- especificación funcional;
- arquitectura técnica;
- plan de seguridad y cumplimiento;
- roadmap;
- backlog inicial;
- instrucciones de arranque para Claude Code.

Las propuestas comerciales, de inversores y de servicios sociales se mantienen como documentación de venta, pero **no condicionan la arquitectura** cuando contienen supuestos ya superados.

---

# 1. Decisiones confirmadas

| Decisión | Resolución |
|---|---|
| Producto principal | Tótem físico vendido como servicio a administraciones públicas |
| Canales posteriores | Web móvil y teléfono, reutilizando núcleo y conectores |
| Territorio del MVP | Castellón, preferiblemente micro-piloto de 1–3 municipios |
| Identidad del usuario | Uso anónimo por defecto, sin cuenta ciudadana |
| Inteligencia artificial | Multimodelo y multimodal: texto, voz e imagen/documentos |
| Integraciones | API oficial cuando exista; navegación asistida como alternativa |
| Persistencia de documentos | No conservar por defecto; tratamiento efímero |
| Autonomía de la IA | La IA guía y prepara; no toma decisiones administrativas ni envía sin confirmación |
| Marca visible | Marca institucional del cliente; Tramitatrón puede quedar como tecnología subyacente |
| Orientación del nuevo desarrollo | Reescritura controlada; no continuar el prototipo línea por línea |

---

# 2. Resumen ejecutivo del producto

Tramitatrón es un **punto público de asistencia digital**, instalado en un ayuntamiento, centro social, oficina comarcal u otra sede institucional, que permite a una persona realizar o preparar trámites digitales mediante una experiencia simplificada.

El usuario puede:

- decir qué necesita con su propia voz;
- elegir un trámite en pantalla;
- escanear o fotografiar un documento;
- revisar los datos extraídos;
- recibir explicaciones comprensibles;
- abrir y completar el portal oficial;
- confirmar cualquier acción relevante;
- imprimir una cita, un justificante o una lista de documentos necesarios;
- pedir ayuda humana cuando el proceso no pueda completarse.

El producto no debe presentarse técnicamente como “un robot que hace trámites”. Debe construirse como una plataforma con tres niveles de ejecución:

1. **Información:** explica requisitos utilizando fuentes oficiales.
2. **Asistencia:** recopila, valida y precompleta; el ciudadano completa los pasos sensibles.
3. **Integración:** ejecuta mediante API o servicio oficial cuando exista autorización técnica y jurídica.

La inteligencia artificial reduce la rigidez de los formularios, interpreta la intención y lee documentos, pero **no elimina la necesidad de conectores**. Cuando no existe una API pública, seguirá siendo necesaria una integración web mantenida, una apertura guiada del portal o una intervención humana.

---

# 3. Estado real del proyecto heredado

## 3.1. Activos recibidos

La documentación interna presenta una beta funcional con interfaz accesible, automatización de citas, OCR y un tótem básico. El código entregado confirma que existe un prototipo Flask orientado a Raspberry Pi con cuatro flujos:

- cita de DNI/pasaporte;
- cita en la Seguridad Social;
- cita en la Agencia Tributaria;
- cita ITV.

También incorpora:

- interfaz táctil;
- español y gallego;
- ajuste del tamaño de letra;
- teclado virtual;
- lectura de pantalla;
- captura frontal y trasera del DNI;
- OCR con Google Cloud Vision;
- Selenium/Chromium para navegar por portales externos;
- pausas para que el usuario seleccione manualmente fecha, hora o tarifa.

El vídeo de estado demuestra una interfaz operativa sobre pantalla táctil, lectura de datos del DNI y transferencia hacia portales oficiales. Por tanto, el prototipo sirve como **prueba de concepto y fuente de conocimiento de los flujos**, no como base de producción.

## 3.2. Qué se puede reutilizar

### Reutilización funcional

- catálogo inicial de trámites;
- conocimiento sobre campos requeridos;
- flujo de lectura frontal/reverso del DNI;
- necesidad de confirmación manual;
- adaptación a uso táctil;
- impresión y salida en papel;
- separación conceptual por organismo;
- cálculo de provincia a partir del código postal;
- experiencia obtenida con Raspberry Pi, cámara y Chromium.

### Reutilización de datos

- tabla de códigos postales, previa comprobación de licencia y actualización;
- reglas deterministas de validación del DNI;
- inventario de campos de formularios;
- textos y contenidos que sigan siendo válidos.

### Reutilización de código

Debe ser selectiva. Se pueden portar pequeñas utilidades validadas, pero no se recomienda incorporar módulos completos sin reescritura y pruebas.

## 3.3. Problemas detectados en la base existente

| Área | Hallazgo | Consecuencia |
|---|---|---|
| Dependencias | No se entrega un fichero reproducible de dependencias | El entorno no se puede reconstruir de forma fiable |
| Importaciones | El código importa `utils.ocr_dni`, pero el fichero entregado se llama `ocr_gcv_dni.py` | El proyecto no arranca sin corrección |
| Configuración | Rutas absolutas a `/home/pi/...`, Chromium y Chromedriver | Acoplamiento al equipo original |
| Seguridad | Clave de sesión incluida en el código y modo debug | No apto para despliegue |
| Frontend | Plantillas con bloques duplicados y HTML inconsistente | Mantenimiento difícil y riesgo de errores |
| Automatización | Selectores Selenium rígidos y esperas con `sleep` | Alta fragilidad ante cambios de portales |
| Seguridad Social | Algunos selectores están descritos como ficticios en comentarios | Flujo no validado como producto |
| CAPTCHA | El flujo del DNI intenta transcribir el CAPTCHA de audio | Riesgo técnico, contractual y reputacional |
| Privacidad | Imágenes de DNI guardadas en rutas estáticas | Riesgo grave si no existe borrado y control |
| Observabilidad | Sin métricas, trazas estructuradas, alertas ni panel | Operación institucional inviable |
| Calidad | Sin pruebas automatizadas ni control de versiones visible | Regresiones impredecibles |
| Arquitectura | Petición web y navegador automatizado comparten proceso | Bloqueo, errores y falta de escalabilidad |
| Datos | No existe política de clasificación, retención o purga | Incompatibilidad con privacidad por diseño |
| Accesibilidad | Existen mejoras visuales, pero no evidencia de auditoría formal | No se puede acreditar cumplimiento |
| Operación | El navegador se abre en el propio tótem y se cierra por tiempos fijos | Experiencia frágil y difícil de soportar |

## 3.4. Conclusión sobre el estado

El proyecto heredado se clasifica como:

- **concepto de producto:** validado;
- **demostrador físico:** validado;
- **experiencia básica:** parcialmente validada;
- **automatizaciones:** demostradas, pero frágiles;
- **producto instalable:** no disponible;
- **seguridad y cumplimiento:** no disponible;
- **operación multi-tótem:** no disponible;
- **escalabilidad institucional:** no disponible.

La decisión correcta es crear un repositorio nuevo y conservar el código antiguo en `/legacy` o en un repositorio archivado únicamente como referencia.

---

# 4. Problema y oportunidad en Castellón

## 4.1. Problema principal

Una parte de la población, especialmente personas mayores o con baja competencia digital, encuentra dificultades para:

- descubrir qué trámite necesita;
- localizar el portal oficial correcto;
- entender requisitos y lenguaje administrativo;
- introducir datos en formularios;
- usar métodos de identificación;
- resolver errores, CAPTCHAs o cambios de interfaz;
- conservar justificantes;
- completar el proceso sin depender de familiares o personal municipal.

## 4.2. Cliente y usuario

**Cliente contratante:** Diputación, Generalitat, mancomunidad, ayuntamiento u organismo público.

**Usuario principal:** ciudadano que utiliza el tótem sin crear una cuenta.

**Usuarios secundarios:**

- personal municipal;
- servicios sociales;
- agente de apoyo local;
- soporte técnico;
- responsables de transformación digital;
- responsables de protección de datos y seguridad;
- responsables políticos que consultan resultados agregados.

## 4.3. Hipótesis comercial que el piloto debe validar

> Una administración pagará por un servicio de asistencia digital si el tótem demuestra uso real, finalización de trámites, reducción de carga informal y una operación controlable.

La tecnología por sí sola no valida el negocio. El piloto debe medir adopción, resolución y coste operativo.

---

# 5. Alcance del MVP

## 5.1. Objetivo del MVP

Construir un sistema instalable en un tótem que, durante un micro-piloto en Castellón, pueda:

1. entender la necesidad del ciudadano por pantalla o voz;
2. ofrecer información fiable desde fuentes oficiales;
3. capturar y extraer datos de documentos de forma efímera;
4. guiar al usuario en dos trámites externos reales;
5. registrar métricas agregadas sin conservar identidad;
6. permitir soporte remoto y actualización;
7. cerrar cada sesión eliminando datos personales.

## 5.2. Alcance funcional mínimo

### Caso A — Orientación y preparación documental

El usuario pregunta, por ejemplo:

- “¿Qué necesito para renovar el DNI?”
- “Quiero pedir cita en el médico.”
- “¿Qué documentos hacen falta para la ITV?”
- “No entiendo esta carta.”

El sistema:

- identifica el trámite;
- consulta contenido oficial previamente indexado;
- explica los pasos;
- muestra fecha de última revisión de la fuente;
- imprime o muestra una lista de requisitos;
- no afirma derechos o resultados que no pueda acreditar.

### Caso B — Cita sanitaria de Atención Primaria GVA

Modo inicial recomendado: **asistido**, no automatización ciega.

El sistema:

- explica qué datos se necesitan;
- captura la tarjeta SIP u otros datos estrictamente necesarios;
- valida formato;
- solicita consentimiento para usar esos datos durante la sesión;
- abre el flujo oficial;
- precompleta cuando técnicamente sea posible;
- entrega el control al usuario en cualquier paso sensible;
- imprime la cita si el portal proporciona confirmación;
- purga los datos.

### Caso C — Cita ITV SITVAL

Modo inicial recomendado: **asistido**.

El sistema:

- pregunta matrícula, tipo de vehículo y preferencias;
- ofrece centros de Castellón;
- abre el sistema oficial;
- precompleta cuando sea estable y permitido;
- solicita confirmación antes de reservar;
- imprime o muestra la cita;
- no almacena matrícula o datos de contacto al terminar.

### Caso D — Lectura y explicación de documento

El ciudadano fotografía o escanea una carta administrativa.

El sistema:

- detecta si contiene datos sensibles;
- extrae texto;
- explica el contenido en lenguaje claro;
- identifica plazos solo cuando aparecen inequívocamente;
- diferencia hechos del documento y explicación de la IA;
- recomienda atención humana para sanciones, recursos, embargos, plazos dudosos o decisiones de alto impacto;
- elimina imagen y texto al cerrar la sesión.

## 5.3. Fuera del MVP

- firma electrónica;
- uso autónomo de certificado digital;
- Cl@ve persistente;
- almacenamiento de credenciales;
- presentación de escritos o solicitudes con efectos jurídicos sin supervisión;
- pagos;
- acceso a expedientes personales;
- empadronamiento completo;
- prestaciones y ayudas con decisión de elegibilidad;
- automatización o elusión de CAPTCHA;
- reconocimiento biométrico;
- perfiles persistentes de ciudadanos;
- recomendaciones proactivas basadas en historial personal;
- uso domiciliario;
- teléfono con IA;
- aplicación móvil nativa.

## 5.4. Priorización de trámites

Cada trámite se puntuará de 1 a 5 en:

- frecuencia esperada;
- utilidad social;
- complejidad;
- disponibilidad de API;
- presencia de CAPTCHA;
- necesidad de firma;
- sensibilidad de datos;
- estabilidad del portal;
- facilidad de prueba;
- riesgo reputacional.

Solo entrarán en el MVP los trámites con alta utilidad y riesgo controlado.

DNI, Seguridad Social y Agencia Tributaria se mantienen en el catálogo futuro, pero no deben ser los primeros conectores automáticos por su fragilidad, autenticación y CAPTCHA.

---

# 6. Principios de producto

1. **Anónimo por defecto.** Sin cuenta, sin expediente permanente y sin memoria entre sesiones.
2. **Consentimiento por acción.** El usuario confirma antes de capturar documentos, enviar datos o reservar.
3. **La IA explica; el sistema valida.** Los datos estructurados se verifican con reglas deterministas.
4. **API antes que navegador.** Una integración oficial tiene prioridad.
5. **Navegador antes que promesas falsas.** Si no existe integración estable, se abre el portal con ayuda.
6. **No se eluden controles.** CAPTCHAs, autenticación y firma quedan en manos del usuario.
7. **Humano disponible.** Siempre debe existir salida hacia soporte o agente local.
8. **Fuentes oficiales.** Las respuestas administrativas deben apoyarse en contenido institucional.
9. **Accesibilidad integral.** Pantalla, voz, mobiliario, privacidad acústica e impresión.
10. **Marca institucional.** El ciudadano debe confiar en el servicio público.
11. **Observabilidad sin vigilancia.** Se miden eventos operativos, no se perfila al ciudadano.
12. **Modularidad.** Cada trámite es un conector intercambiable.
13. **Degradación segura.** Si falla la IA, el usuario accede al catálogo y a guías estáticas.
14. **No dependencia de un modelo.** El proveedor de IA puede cambiarse.
15. **No sobreautomatizar.** Un proceso guiado robusto vale más que un robot frágil.

---

# 7. Modos de ejecución de un trámite

## 7.1. Modo INFORMACIÓN

No transmite datos personales a un portal externo.

Ejemplos:

- requisitos;
- horarios;
- documentos;
- ubicación;
- instrucciones;
- descarga de formulario público.

## 7.2. Modo ASISTIDO

El sistema recopila y valida datos, abre el portal oficial y puede precompletar campos. El usuario:

- resuelve CAPTCHA;
- se autentica;
- elige hora;
- acepta condiciones;
- confirma el envío.

Es el modo predeterminado cuando no existe API pública.

## 7.3. Modo INTEGRADO

El sistema usa una API o servicio oficial documentado. Requiere:

- autorización;
- contrato o convenio si procede;
- especificación estable;
- trazabilidad;
- pruebas;
- acuerdo de responsabilidades.

## 7.4. Modo DERIVACIÓN

El sistema no puede completar el trámite. Entrega:

- explicación;
- documentación necesaria;
- teléfono;
- oficina;
- enlace o QR;
- opción de ayuda humana;
- código de incidencia anónimo.

---

# 8. Arquitectura funcional

```text
┌──────────────────────────────────────────────────────────────┐
│                        TÓTEM / KIOSK                         │
│  Pantalla táctil · Voz · Cámara · Escáner · Impresora       │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼──────────────────────────────────┐
│                     API DE TRAMITATRÓN                       │
│ Sesión efímera · Políticas · Consentimiento · Orquestación   │
└───────────────┬────────────────────┬─────────────────────────┘
                │                    │
┌───────────────▼───────────┐  ┌─────▼─────────────────────────┐
│  GATEWAY MULTIMODELO      │  │ REGISTRO DE TRÁMITES         │
│ texto · visión · voz      │  │ API · asistido · derivación  │
└───────────────┬───────────┘  └─────┬─────────────────────────┘
                │                    │
┌───────────────▼───────────┐  ┌─────▼─────────────────────────┐
│ SERVICIO DOCUMENTAL       │  │ WORKERS DE CONECTORES        │
│ captura · OCR · validación│  │ API clients · Playwright     │
│ redacción · purga         │  │ navegador aislado            │
└───────────────┬───────────┘  └─────┬─────────────────────────┘
                │                    │
┌───────────────▼────────────────────▼─────────────────────────┐
│ DATOS OPERATIVOS NO IDENTIFICATIVOS                          │
│ PostgreSQL · métricas · incidencias · catálogo · versiones  │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│ PANEL INSTITUCIONAL Y OPERACIÓN                              │
│ KPIs · salud de tótems · contenidos · conectores · soporte  │
└──────────────────────────────────────────────────────────────┘
```

---

# 9. Arquitectura técnica propuesta

## 9.1. Enfoque general

Monorepo modular con frontend TypeScript y backend Python.

### Frontend del tótem

- Next.js o React con TypeScript.
- PWA instalable y ejecutable en modo kiosco.
- i18n desde el inicio.
- almacenamiento local mínimo.
- shell capaz de mostrar guías estáticas cuando el backend no responde.
- comunicación con periféricos mediante un agente local.

### Backend

- Python 3.12+.
- FastAPI.
- Pydantic para esquemas y validación.
- PostgreSQL para configuración y métricas no personales.
- Redis para sesiones con TTL y colas ligeras.
- workers separados para tareas documentales y navegación.
- OpenTelemetry para trazas.
- almacenamiento temporal cifrado con política automática de borrado.

### Navegación automatizada

- Playwright.
- proceso independiente del API.
- contexto de navegador nuevo por sesión.
- dominios permitidos por lista blanca.
- grabación y capturas desactivadas por defecto cuando haya datos personales.
- secretos fuera del código.
- no resolución automática de CAPTCHA.

### Panel institucional

- aplicación web separada o espacio `/admin`.
- roles: soporte, gestor institucional, administrador técnico.
- métricas agregadas;
- estado de dispositivos;
- catálogo y versión de trámites;
- incidencias;
- auditoría operativa.

## 9.2. Razón de la combinación TypeScript + Python

TypeScript es adecuado para la interfaz, PWA y control de experiencia. Python reduce fricción en:

- IA;
- visión;
- extracción documental;
- validación;
- automatización;
- servicios API.

No se recomienda una arquitectura de microservicios extensa en el MVP. Se utilizará un **monolito modular** y un worker de navegador separado. Separar más servicios antes de validar el piloto aumentaría el coste sin aportar valor.

## 9.3. Estructura de repositorio

```text
tramitatron/
├─ apps/
│  ├─ kiosk/                    # interfaz del tótem
│  └─ admin/                    # panel institucional
├─ services/
│  ├─ api/                      # FastAPI, sesiones, políticas
│  ├─ browser-worker/           # Playwright y conectores web
│  └─ device-agent/             # cámara, escáner, impresora, watchdog
├─ packages/
│  ├─ ui/                       # componentes accesibles
│  ├─ contracts/                # esquemas OpenAPI/JSON
│  ├─ i18n/                     # castellano y valenciano
│  └─ config/                   # configuración compartida
├─ connectors/
│  ├─ gva_health/
│  ├─ sitval/
│  └─ official_content/
├─ knowledge/
│  ├─ sources.yaml
│  ├─ snapshots/
│  └─ ingestion/
├─ infra/
│  ├─ docker/
│  ├─ terraform/
│  └─ monitoring/
├─ docs/
│  ├─ adr/
│  ├─ security/
│  ├─ accessibility/
│  └─ operations/
├─ tests/
│  ├─ e2e/
│  ├─ accessibility/
│  ├─ connectors/
│  └─ privacy/
├─ legacy/                      # solo referencia; no importar
├─ .env.example
├─ docker-compose.yml
├─ Makefile
├─ CLAUDE.md
└─ README.md
```

---

# 10. Gateway multimodelo y multimodal

## 10.1. Objetivo

Evitar que la lógica de negocio dependa de un proveedor o modelo concreto.

```python
class ModelGateway(Protocol):
    async def classify_intent(self, request: IntentRequest) -> IntentResult: ...
    async def explain_official_content(self, request: ExplainRequest) -> ExplainResult: ...
    async def extract_document(self, request: DocumentRequest) -> DocumentResult: ...
    async def transcribe(self, request: AudioRequest) -> TranscriptResult: ...
    async def synthesize(self, request: SpeechRequest) -> SpeechResult: ...
```

## 10.2. Reglas de selección de modelo

- modelo ligero para clasificación de intención;
- modelo de visión para documentos;
- modelo más potente para explicación compleja;
- TTS/STT específicos para voz;
- fallback configurado por tarea;
- presupuesto máximo por sesión;
- tiempo máximo por operación;
- circuit breaker por proveedor.

## 10.3. Salidas estructuradas

La IA nunca debe devolver una orden de ejecución libre. Debe producir objetos validados:

```json
{
  "intent": "BOOK_HEALTH_APPOINTMENT",
  "confidence": 0.94,
  "required_fields": ["sip_number", "birth_date"],
  "next_action": "ASK_CONSENT",
  "risk_level": "A2",
  "source_ids": ["gva-health-appointment"]
}
```

## 10.4. Política de proveedores

Antes de enviar datos personales a un proveedor se debe verificar:

- región de procesamiento;
- contrato de encargado/subencargado;
- retención;
- uso o no para entrenamiento;
- cifrado;
- borrado;
- transferencias internacionales;
- certificaciones;
- posibilidad de desactivar logs;
- compatibilidad con ENS y requisitos del contratante.

Para el MVP se diseñará el gateway, pero se habilitará un proveedor principal y uno de respaldo. Integrar tres proveedores completos desde el primer día sería trabajo innecesario.

---

# 11. Gestión documental

## 11.1. Enfoque híbrido

No se debe sustituir todo OCR por una llamada a un modelo multimodal. La solución robusta combina:

1. detección y recorte del documento;
2. control de calidad de imagen;
3. OCR o extracción documental;
4. modelo multimodal para normalizar e interpretar;
5. validadores deterministas;
6. revisión visual por el usuario.

## 11.2. Flujo de captura

```text
CAPTURE
  → QUALITY_CHECK
  → CLASSIFY_DOCUMENT
  → EXTRACT
  → VALIDATE
  → REDACT_IF_NEEDED
  → USER_CONFIRM
  → USE_IN_SESSION
  → PURGE
```

## 11.3. Clases iniciales

- DNI/NIE: solo los campos necesarios para el trámite.
- tarjeta SIP.
- carta administrativa genérica.
- permiso de circulación o ficha técnica: fase posterior.

## 11.4. Reglas

- No guardar en la carpeta pública del frontend.
- No reutilizar una captura en otra sesión.
- Cifrado temporal.
- TTL objetivo: 15 minutos.
- Borrado inmediato al finalizar sesión.
- El log solo conserva tipo de documento, éxito de extracción y duración.
- Mostrar todos los datos al ciudadano antes de usarlos.
- La IA no corrige silenciosamente un dato de identidad.

## 11.5. Confianza y validación

Cada campo tendrá:

- valor;
- confianza;
- origen;
- validación;
- necesidad de revisión.

```json
{
  "field": "sip_number",
  "value": "12345678",
  "confidence": 0.91,
  "validator": "sip_format_v1",
  "status": "REVIEW_REQUIRED"
}
```

---

# 12. Motor de trámites

## 12.1. Registro declarativo

Cada trámite se define mediante metadatos y un adaptador.

```yaml
id: gva.health.primary-care.appointment
name:
  es: Cita de atención primaria
  ca-valencia: Cita d'atenció primària
territory: ES-VC-CS
execution_mode: assisted
risk_class: A2
official_sources:
  - https://www.san.gva.es/
required_fields:
  - sip_number
  - birth_date
confirmation_required: true
captcha_policy: user_only
document_retention: none
connector:
  type: playwright
  package: connectors.gva_health
healthcheck:
  cadence: daily
  synthetic_data_only: true
```

## 12.2. Estados

```text
DISCOVERED
→ EXPLAINED
→ CONSENTED
→ COLLECTING
→ VALIDATED
→ READY_TO_EXECUTE
→ USER_CONFIRMATION
→ EXECUTING
→ USER_HANDOFF
→ COMPLETED | FAILED | ABANDONED
→ PURGED
```

## 12.3. Contrato del conector

```python
class TransactionConnector(Protocol):
    metadata: ConnectorMetadata

    async def preflight(self, context: SessionContext) -> PreflightResult: ...
    async def validate(self, data: dict) -> ValidationResult: ...
    async def prepare(self, data: dict) -> PreparedAction: ...
    async def execute(self, action: PreparedAction) -> ExecutionResult: ...
    async def resume_after_user(self, token: str) -> ExecutionResult: ...
    async def healthcheck(self) -> HealthcheckResult: ...
```

## 12.4. Política API primero

Orden obligatorio:

1. API pública documentada.
2. API mediante convenio.
3. enlace profundo con parámetros admitidos.
4. navegación web asistida.
5. guía estática y derivación.

No se debe inspeccionar una API privada de una aplicación ni depender de endpoints no documentados sin autorización.

## 12.5. Reglas para Playwright

- selectores semánticos y por roles antes que XPath;
- Page Object por portal;
- trazas técnicas sin PII;
- datos sintéticos en pruebas;
- detección de cambios;
- `healthcheck` diario sin reservar;
- parada segura ante divergencia;
- límite de tiempo;
- captura de error redactada;
- versión del conector;
- feature flag para deshabilitarlo;
- intervención del usuario en CAPTCHA, firma, autenticación y confirmación.

---

# 13. Sesión anónima y modelo de datos

## 13.1. Sesión ciudadana

- identificador aleatorio;
- no vinculado a nombre o documento;
- TTL de 20 minutos de inactividad;
- prolongación explícita si el trámite está abierto;
- cierre visible;
- purga automática;
- reinicio del tótem entre usuarios;
- bloqueo de retorno a páginas anteriores con datos.

## 13.2. Clasificación de datos

| Nivel | Ejemplos | Política |
|---|---|---|
| A0 | intención, idioma, tipo de trámite | métrica agregable |
| A1 | teléfono, correo, matrícula | solo sesión; no log |
| A2 | DNI, SIP, fecha de nacimiento, documentos | cifrado efímero y consentimiento |
| A3 | certificados, Cl@ve, firma, credenciales | fuera del MVP |

## 13.3. Datos persistentes permitidos

### `kiosks`

- id;
- tenant;
- municipio;
- versión;
- estado;
- última conexión;
- periféricos;
- configuración no sensible.

### `transaction_catalog`

- id;
- versión;
- estado;
- territorio;
- modo;
- fuentes;
- riesgo;
- última verificación.

### `session_metrics`

- session_id pseudónimo;
- kiosk_id;
- inicio y fin;
- idioma;
- trámite;
- estado final;
- duración;
- incidencias;
- sin campos personales.

### `incidents`

- código;
- componente;
- conector;
- severidad;
- error técnico redactado;
- timestamps;
- resolución.

### `knowledge_sources`

- URL oficial;
- organismo;
- fecha de consulta;
- hash;
- versión;
- estado;
- próxima revisión.

## 13.4. Datos que no deben persistir

- nombre;
- DNI/NIE;
- número SIP;
- dirección;
- fecha de nacimiento;
- imagen de documentos;
- audio bruto;
- contenido de cartas;
- matrícula;
- teléfonos y correos;
- cookies o tokens de portales externos.

Una excepción requerirá una decisión de arquitectura, base jurídica, registro de tratamiento y actualización de la EIPD.

---

# 14. Interfaz y accesibilidad

## 14.1. Idiomas

MVP:

- castellano;
- valenciano.

La selección se realiza al inicio y se reinicia al acabar.

## 14.2. Diseño de pantalla

- resolución objetivo configurable;
- botones grandes;
- máximo de tres decisiones principales por pantalla;
- una pregunta por paso;
- texto principal entre 24 y 32 px según distancia;
- contraste alto;
- icono + texto;
- progreso visible;
- botón permanente “Atrás”;
- botón permanente “Terminar y borrar mis datos”;
- lectura en voz alta;
- control de volumen;
- repetición;
- ausencia de scroll complejo;
- teclado en pantalla solo cuando sea imprescindible.

## 14.3. Voz

La voz no debe ser el único canal.

- pulsar para hablar;
- indicador claro de grabación;
- transcripción visible;
- confirmación antes de usar;
- botón para borrar;
- auricular o altavoz direccional;
- textos breves;
- posibilidad de desactivar.

## 14.4. Accesibilidad física del tótem

Debe definirse con fabricante o integrador:

- altura y alcance desde silla de ruedas;
- pantalla inclinable o posición adecuada;
- espacio libre frontal;
- cámara accesible;
- bandeja de documentos;
- impresora alcanzable;
- conexiones no accesibles al público;
- auriculares o privacidad acústica;
- superficie sin reflejos;
- instrucciones visibles;
- posibilidad de uso sentado.

## 14.5. Pruebas

- navegación por teclado;
- lector de pantalla;
- contraste;
- zoom 200%;
- tamaño de objetivos táctiles;
- comprensión con usuarios mayores;
- valenciano y castellano;
- tiempos;
- errores;
- recuperación;
- auditoría formal antes del piloto institucional.

Objetivo interno: WCAG 2.2 AA, EN 301 549 aplicable y revisión conforme al marco español del sector público.

---

# 15. Seguridad, privacidad y cumplimiento

## 15.1. Marcos a contemplar

- RGPD.
- LOPDGDD.
- Real Decreto 1112/2018 de accesibilidad.
- Real Decreto 311/2022, Esquema Nacional de Seguridad.
- Esquema Nacional de Interoperabilidad cuando proceda.
- Reglamento europeo de Inteligencia Artificial.
- normativa de contratación y condiciones de cada portal.
- políticas del organismo responsable.

No se presupone cumplimiento por diseño técnico. Debe existir revisión legal y de seguridad antes del piloto.

## 15.2. Responsabilidades

Debe acordarse contractualmente:

- quién es responsable del tratamiento;
- quién actúa como encargado;
- subencargados;
- proveedores de IA;
- proveedor cloud;
- soporte remoto;
- fabricante;
- gestión de incidencias;
- atención de derechos;
- notificación de brechas.

## 15.3. EIPD

Se recomienda realizar una Evaluación de Impacto antes de procesar documentos reales porque concurren:

- población potencialmente vulnerable;
- documentos de identidad;
- datos sanitarios;
- espacio público;
- IA;
- posible monitorización operativa;
- múltiples proveedores.

## 15.4. Medidas mínimas

- arranque seguro del dispositivo;
- cifrado de disco;
- usuario sin privilegios;
- puertos bloqueados;
- allowlist de dominios;
- actualizaciones firmadas;
- MDM o gestión remota;
- VPN o canal de administración;
- autenticación fuerte para soporte;
- no acceso remoto silencioso a una sesión ciudadana;
- separación de entornos;
- secretos en vault;
- SBOM;
- escaneo de dependencias;
- logs centralizados;
- alertas;
- backups únicamente de configuración y métricas;
- ejercicio de borrado;
- respuesta a incidentes;
- pentest previo.

## 15.5. Política de IA

La IA:

- debe identificarse como asistencia automatizada;
- no toma decisiones administrativas;
- no determina elegibilidad final;
- no inventa requisitos;
- cita fuente y fecha;
- informa cuando no tiene certeza;
- no ejecuta herramientas fuera del catálogo;
- no recibe más datos de los necesarios;
- se somete a supervisión humana;
- registra versión de prompt y modelo sin guardar conversación personal.

## 15.6. Riesgo de clasificación conforme al AI Act

El diseño debe mantenerse como **asistente de información y tramitación**, sin adoptar o recomendar decisiones que determinen acceso a prestaciones o derechos. Si se amplía hacia elegibilidad, priorización o decisión sobre personas, será necesaria una evaluación específica de clasificación y obligaciones, incluida potencial evaluación de derechos fundamentales.

---

# 16. Conocimiento oficial y RAG

## 16.1. Principio

El modelo no debe responder de memoria sobre trámites cambiantes. Debe usar una base de conocimiento con fuentes oficiales versionadas.

## 16.2. Ingesta

- URLs permitidas;
- descarga programada;
- extracción;
- segmentación;
- hash;
- fecha;
- organismo;
- territorio;
- vigencia;
- revisión humana para contenido crítico;
- despublicación automática si la fuente desaparece.

## 16.3. Respuesta

Toda respuesta administrativa mostrará:

- organismo;
- título de fuente;
- fecha de actualización o consulta;
- enlace/QR;
- aviso si el contenido puede haber cambiado.

## 16.4. Política de actualización

- contenido sanitario y citas: diario o semanal;
- requisitos nacionales: semanal;
- convocatorias y ayudas: según fuente;
- contenido estático: mensual;
- alerta ante cambio de hash;
- revisión humana si cambian pasos críticos.

## 16.5. No incluido inicialmente

No se construirá un buscador universal de subvenciones. Abrir ese alcance retrasaría el MVP y elevaría mucho el riesgo de información desactualizada.

---

# 17. Periféricos y agente local del dispositivo

## 17.1. Funciones del `device-agent`

- estado de cámara;
- captura;
- escáner;
- impresión;
- nivel de papel;
- audio;
- reinicio del navegador;
- watchdog;
- actualización;
- borrado local;
- telemetría;
- test de conectividad.

## 17.2. API local

```text
GET  /device/health
POST /device/camera/capture
POST /device/scanner/scan
POST /device/printer/print
POST /device/session/purge
POST /device/kiosk/restart
```

Debe escuchar solo en localhost o socket local y autenticar al frontend.

## 17.3. Modo kiosco

- Chromium gestionado;
- navegación externa en contexto controlado;
- sin descargas libres;
- sin barra de direcciones;
- retorno automático a inicio;
- limpieza de cookies y almacenamiento;
- reinicio diario;
- bloqueo de combinaciones de teclado;
- pantalla de fuera de servicio;
- número de soporte.

---

# 18. Portal institucional y KPIs

## 18.1. KPIs del piloto

### Uso

- sesiones;
- trámites iniciados;
- trámites completados;
- usuarios que abandonan;
- idioma;
- franja horaria.

### Eficiencia

- duración;
- pasos;
- tasa de éxito;
- errores;
- derivaciones;
- reintentos.

### Operación

- disponibilidad;
- fallos de periféricos;
- fallos de conector;
- tiempo de resolución;
- versión desplegada.

### Impacto

- satisfacción 1–5;
- “¿Habría necesitado ayuda de otra persona?”;
- desplazamiento evitado declarado;
- percepción del personal municipal;
- coste por trámite completado.

## 18.2. Métricas prohibidas

- nombres;
- identificación individual;
- conversaciones completas;
- imágenes;
- perfil sociodemográfico inferido;
- salud inferida;
- seguimiento entre sesiones.

## 18.3. Cuadro de mando

Filtros:

- periodo;
- municipio;
- tótem;
- trámite;
- estado.

Exportación:

- CSV;
- PDF agregado;
- sin datos personales.

---

# 19. Observabilidad y soporte

## 19.1. Telemetría

- trazas por sesión pseudónima;
- métricas RED;
- eventos del conector;
- healthcheck de tótem;
- healthcheck de portales;
- estado de cola;
- consumo de IA;
- error budget.

## 19.2. Severidades

| Severidad | Ejemplo | Objetivo |
|---|---|---|
| S1 | exposición de datos o control del tótem | contención inmediata |
| S2 | tótem inutilizable | respuesta prioritaria |
| S3 | un trámite no funciona | desactivar conector y derivar |
| S4 | error menor de contenido o interfaz | backlog |

## 19.3. Degradación

- Si falla la IA: catálogo y guías estáticas.
- Si falla un conector: información + enlace/QR + soporte.
- Si falla la impresora: QR o SMS solo con consentimiento.
- Si falla Internet: guía offline, sin captura de documentos.
- Si falla el backend: pantalla de incidencia, sin mostrar datos previos.

---

# 20. Estrategia de despliegue

## 20.1. Desarrollo

- Docker Compose.
- datos sintéticos.
- simuladores de cámara e impresora.
- portales externos en modo mock.
- CI en cada pull request.

## 20.2. Piloto técnico

- backend en región UE;
- un tótem;
- 2 conectores;
- soporte intensivo;
- feature flags;
- actualización remota;
- acceso restringido durante pruebas.

## 20.3. Piloto institucional

- 1–3 municipios;
- contrato y roles definidos;
- EIPD;
- plan ENS;
- auditoría de accesibilidad;
- plan de comunicación;
- formación;
- métricas;
- periodo 8–12 semanas.

## 20.4. Producción provincial

Solo después de:

- estabilidad de conectores;
- satisfacción;
- coste operativo conocido;
- proceso de soporte probado;
- seguridad;
- cumplimiento;
- hardware homologado;
- plan de escalado.

---

# 21. Plan de desarrollo

## 21.1. Estimación realista

### Un desarrollador apoyado por Claude Code

- demo moderna: 6–8 semanas;
- piloto técnico controlado: 10–12 semanas;
- piloto institucional razonable: 14–18 semanas;
- producto provincial: posterior al piloto.

Prometer un producto institucional completo en 4–8 semanas replicaría los problemas del prototipo.

## 21.2. Fases

### Fase 0 — Descubrimiento y cimentación — 1 semana

- crear repositorio;
- archivar legado;
- seleccionar 1–3 municipios;
- seleccionar dos trámites;
- validar hardware;
- matriz legal;
- arquitectura y ADR;
- configurar CI.

### Fase 1 — Núcleo anónimo y UI — 2–3 semanas

- PWA;
- i18n;
- accesibilidad;
- sesiones;
- consentimiento;
- catálogo;
- guía estática;
- model gateway;
- modo simulador.

### Fase 2 — Documentos y conocimiento — 2–3 semanas

- cámara/escáner;
- servicio efímero;
- extracción DNI/SIP;
- validación;
- RAG oficial;
- explicación de cartas;
- purga.

### Fase 3 — Dos conectores reales — 3–4 semanas

- GVA Salud;
- SITVAL;
- Playwright;
- handoff;
- confirmación;
- impresión;
- healthchecks.

### Fase 4 — Operación y panel — 2–3 semanas

- portal;
- métricas;
- dispositivos;
- incidencias;
- logs;
- alertas;
- actualización remota.

### Fase 5 — Hardening y piloto — 2–4 semanas

- E2E;
- accesibilidad;
- seguridad;
- privacidad;
- pruebas con usuarios;
- manuales;
- despliegue.

---

# 22. Backlog inicial para Claude Code

## EPIC 0 — Bootstrap

### TT-001 Crear monorepo

**Criterios de aceptación**

- estructura definida;
- `docker compose up` arranca kiosk, API, PostgreSQL y Redis;
- linters y formateadores;
- tests mínimos;
- README;
- `.env.example`;
- no secretos.

### TT-002 Añadir CI

- lint;
- typecheck;
- tests;
- build;
- dependency scan;
- secret scan.

### TT-003 Archivar legado

- copiar código antiguo a `/legacy`;
- README con advertencia;
- no importarlo;
- inventario de utilidades portables.

## EPIC 1 — Kiosco

### TT-101 Pantalla de inicio

- castellano/valenciano;
- voz o botones;
- tamaño de letra;
- alto contraste;
- “terminar sesión”.

### TT-102 Catálogo

- tarjetas;
- búsqueda por voz;
- modo offline;
- estados de disponibilidad.

### TT-103 Flujo paso a paso

- una pregunta por pantalla;
- progreso;
- atrás;
- confirmar;
- cancelar;
- timeout accesible.

## EPIC 2 — Sesión y privacidad

### TT-201 Sesión efímera

- UUID;
- TTL;
- purga;
- no cookies persistentes;
- test de aislamiento.

### TT-202 Consentimiento

- captura documental;
- uso de IA;
- transmisión a portal;
- confirmación final.

### TT-203 Privacy test suite

- búsqueda de PII en logs;
- purga;
- cachés;
- almacenamiento del navegador;
- ficheros temporales.

## EPIC 3 — IA

### TT-301 Model gateway

- interfaz;
- proveedor principal;
- fallback;
- timeout;
- coste;
- structured output.

### TT-302 Clasificación de intención

- catálogo cerrado;
- umbral de confianza;
- clarificación;
- derivación.

### TT-303 Asistente oficial

- RAG;
- fuentes;
- fecha;
- respuesta breve;
- límites.

## EPIC 4 — Documentos

### TT-401 Device agent simulator

- captura de fichero;
- escáner simulado;
- impresión PDF simulada.

### TT-402 Extracción SIP

- imagen;
- campos;
- confianza;
- validación;
- revisión.

### TT-403 Extracción DNI

- campos mínimos;
- sin persistencia;
- validación de letra;
- revisión.

### TT-404 Explicación de carta

- OCR;
- resumen;
- plazos detectados;
- alerta de alto riesgo;
- purga.

## EPIC 5 — Conectores

### TT-501 Registro de trámites

- YAML;
- esquema;
- versionado;
- enable/disable.

### TT-502 Worker Playwright

- aislamiento;
- allowlist;
- eventos;
- timeout;
- handoff.

### TT-503 GVA Salud

- preflight;
- recogida de datos;
- navegación asistida;
- CAPTCHA/confirmación usuario;
- receipt.

### TT-504 SITVAL

- centros Castellón;
- matrícula;
- navegación;
- confirmación;
- receipt.

### TT-505 Healthchecks

- sintéticos;
- no reserva;
- alerta por cambio.

## EPIC 6 — Operación

### TT-601 Registro de tótems

### TT-602 Dashboard de KPIs

### TT-603 Incidencias y soporte

### TT-604 Actualización y versión

### TT-605 Estado de periféricos

## EPIC 7 — Calidad y cumplimiento

### TT-701 Tests de accesibilidad

### TT-702 Threat model

### TT-703 EIPD técnica

### TT-704 Plan ENS

### TT-705 Pentest

### TT-706 Prueba con usuarios

---

# 23. Casos de aceptación end-to-end

## E2E-01 Orientación sin datos

1. El usuario inicia en castellano.
2. Dice “quiero pedir cita para el médico”.
3. El sistema identifica GVA Salud.
4. Explica requisitos con fuente.
5. El usuario imprime la lista.
6. La sesión se cierra.
7. No queda audio, texto libre ni PII.

## E2E-02 SIP

1. Se solicita consentimiento.
2. Se captura la tarjeta.
3. Se extraen datos.
4. El usuario corrige un campo.
5. Se abre el portal.
6. El usuario confirma.
7. Se imprime resultado.
8. Se purgan imagen y campos.

## E2E-03 Conector caído

1. El healthcheck marca SITVAL no disponible.
2. El catálogo muestra “temporalmente no disponible”.
3. Se ofrece teléfono, enlace QR y requisitos.
4. No se intenta automatizar.
5. Se crea incidencia sin PII.

## E2E-04 Carta sensible

1. El usuario escanea una carta de embargo.
2. El sistema resume hechos visibles.
3. Destaca fecha y organismo.
4. No recomienda un recurso jurídico concreto.
5. Deriva a atención humana.
6. El documento se elimina.

## E2E-05 Aislamiento

1. Usuario A introduce datos.
2. Finaliza.
3. Usuario B inicia.
4. No aparece ningún dato, historial, autocompletado o cookie del usuario A.

---

# 24. Riesgos críticos

| Riesgo | Probabilidad | Impacto | Tratamiento |
|---|---:|---:|---|
| Cambios en portales | Alta | Alto | modo asistido, healthchecks y feature flags |
| No existencia de APIs públicas | Alta | Alto | arquitectura por niveles, convenio futuro |
| Automatización bloqueada | Alta | Alto | no depender del éxito automático |
| Bajo uso | Media-Alta | Alto | agente local, selección correcta y comunicación |
| Fuga de documentos | Media | Crítico | efímero, cifrado, pruebas de purga |
| Alucinación de requisitos | Media | Alto | RAG oficial, citas y límites |
| Incumplimiento de accesibilidad | Media | Alto | auditoría y pruebas con usuarios |
| Sobrecoste de soporte | Media | Alto | métricas y limitar trámites |
| Exceso de alcance | Alta | Alto | dos conectores y criterios estrictos |
| Dependencia de proveedor IA | Media | Medio | gateway y exportabilidad |
| Clasificación regulatoria de IA | Baja-Media | Alto | no decidir derechos, evaluación jurídica |
| Hardware heterogéneo | Media | Medio | modelo de referencia y device-agent |
| Privacidad acústica | Media | Medio-Alto | auricular, volumen y diseño del espacio |
| Venta pública lenta | Alta | Alto | micro-piloto y evidencia de impacto |

---

# 25. Decisiones pendientes no bloqueantes

Estas decisiones deben cerrarse durante la Fase 0, pero no impiden crear el repositorio:

1. Municipios exactos del micro-piloto.
2. Administración que actuará como patrocinador.
3. Modelo de hardware.
4. Proveedor cloud.
5. Proveedor principal de IA.
6. Segundo conector definitivo si SITVAL no resulta viable.
7. Impresión térmica o A4.
8. Agente local obligatorio u opcional.
9. Canal de soporte.
10. Métricas contractuales.

Valores por defecto para empezar:

```yaml
pilot:
  region: ES-VC-CS
  municipalities: TBD
  kiosk_count: 1
  languages: [es, ca-valencia]
  connectors:
    - gva_health_primary_care
    - sitval_appointment
  channels: [kiosk]
  identity: anonymous
  retention: none
```

---

# 26. Criterios para elegir municipios

Puntuar:

- población mayor;
- distancia a servicios;
- espacio municipal;
- conectividad;
- personal colaborador;
- volumen de consultas;
- visibilidad;
- diversidad territorial;
- facilidad logística;
- compromiso político;
- posibilidad de medir carga municipal.

No elegir cinco municipios en el primer piloto. Un despliegue de 1–3 permite corregir producto y operación antes de multiplicar errores.

---

# 27. Estrategia de negocio coherente con el producto

El tótem es el canal comercial principal, pero la propiedad intelectual valiosa es:

- motor de sesiones;
- catálogo;
- conectores;
- conocimiento oficial;
- capa de IA;
- operación;
- cumplimiento;
- métricas.

La arquitectura debe permitir, sin rehacer el núcleo:

- web móvil;
- teléfono;
- tablet de agente social;
- punto móvil;
- marca blanca;
- SDK o API.

No se desarrollarán esos canales durante el MVP.

---

# 28. Fuentes internas del proyecto

- `Tramitatron RFP.pdf`
- `PROYECTO Accesibilidad UVIGO.rar`
- `Estado_20250602.mp4`
- `Resumen_Ejecutivo_Tramitatron.pdf`
- `Tramitatron_Investor_Memo.pdf`
- `Tramitatron_Memoria_Master_Consejo.pdf`
- `Tramitatron_OnePage.pdf`
- `Tramitatron_Propuesta_Administracion_Resumen.pdf`
- `Tramitatron_Propuesta_Servicios_Sociales.pdf`
- `Tramitatron_Propuesta_Venta_Administracion_v2.pdf`

---

# 29. Fuentes oficiales de referencia

- Real Decreto 1112/2018, accesibilidad del sector público:  
  https://www.boe.es/buscar/act.php?id=BOE-A-2018-12699

- Real Decreto 311/2022, Esquema Nacional de Seguridad:  
  https://www.boe.es/buscar/act.php?id=BOE-A-2022-7191

- AEPD, gestión del riesgo y EIPD:  
  https://www.aepd.es/derechos-y-deberes/cumple-tus-deberes/medidas-de-cumplimiento/realizacion-de-evaluaciones-de

- Reglamento (UE) 2024/1689, Reglamento de Inteligencia Artificial:  
  https://eur-lex.europa.eu/eli/reg/2024/1689/oj?locale=es

- Esquema Nacional de Interoperabilidad:  
  https://administracionelectronica.gob.es/ctt/eni

- Portal del Paciente de la Conselleria de Sanidad:  
  https://www.san.gva.es/es/web/portal-del-paciente

- Cita previa de la Generalitat Valenciana:  
  https://sede.gva.es/es/cita-previa

- SITVAL:  
  https://sitval.com/

- Diputación de Castellón, administración electrónica:  
  https://www.dipcas.es/es/administracionelectronica.html

---

# 30. Prompt de arranque para Claude Code

```text
Vas a iniciar un repositorio nuevo llamado `tramitatron`.

Lee íntegramente el documento `TRAMITATRON_MASTER_PRD.md`.

Reglas obligatorias:

1. No reutilices el código de `/legacy` salvo pequeñas funciones que primero cubras con tests.
2. No añadas funcionalidades fuera del MVP.
3. El sistema es anónimo por defecto.
4. No guardes PII ni documentos en logs, base de datos o almacenamiento persistente.
5. No automatices CAPTCHAs, firma, Cl@ve o credenciales.
6. Todas las acciones externas requieren schemas tipados y política de confirmación.
7. La IA no puede invocar URLs arbitrarias.
8. Usa un monolito modular y un worker separado para Playwright.
9. Implementa castellano y valenciano desde el primer componente.
10. Añade tests y documentación en cada entrega.
11. No elijas un proveedor IA dentro del dominio; usa un gateway.
12. Prioriza una demo local reproducible con Docker.

Primera entrega:

- estructura de monorepo;
- ADR-001 de arquitectura;
- `docker-compose.yml`;
- FastAPI con `/health`;
- app kiosk con pantalla de idioma;
- sesión efímera;
- botón de cierre y purga;
- modelo declarativo de catálogo;
- conector mock;
- CI;
- README con instrucciones.

Antes de escribir código:
- crea un plan de implementación;
- enumera supuestos;
- detecta contradicciones;
- plantea solo preguntas que bloqueen la primera entrega.

No desarrolles aún los conectores reales de GVA o SITVAL hasta que el núcleo, los mocks y las pruebas de privacidad funcionen.
```

---

# 31. Definición de terminado del MVP

El MVP estará terminado cuando:

- un tótem nuevo pueda instalarse desde documentación;
- el sistema arranque sin secretos incluidos;
- castellano y valenciano funcionen;
- una sesión no deje datos a la siguiente;
- la cámara y la impresora tengan simulador y driver;
- el asistente responda con fuentes oficiales;
- dos conectores funcionen en modo asistido;
- los conectores puedan deshabilitarse remotamente;
- exista panel de salud y KPIs;
- existan pruebas de accesibilidad y privacidad;
- exista proceso de soporte;
- exista plan de EIPD y ENS;
- se hayan realizado pruebas con usuarios;
- no haya automatización de CAPTCHA;
- se pueda demostrar borrado;
- se pueda desplegar una actualización controlada;
- el coste por sesión y el coste operativo sean medibles.

---

# 32. Próximo hito

**Hito 1: repositorio ejecutable y núcleo anónimo.**

Entregables:

1. monorepo;
2. Docker local;
3. frontend kiosco;
4. API;
5. sesión efímera;
6. catálogo mock;
7. gateway IA mock;
8. simulador de periféricos;
9. pruebas de aislamiento;
10. ADR y documentación.

Hasta completar este hito no se debe trabajar en automatizaciones reales.

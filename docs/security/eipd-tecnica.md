# EIPD técnica — Tramitatrón (BORRADOR)

- **Ticket:** TT-703 (EPIC 7)
- **Estado:** BORRADOR técnico para revisión del Delegado de Protección de
  Datos (DPD) y asesoría jurídica
- **Fecha:** 2026-07-21
- **Base metodológica:** Art. 35 RGPD; guía de la AEPD para Evaluaciones de
  Impacto; LOPDGDD.
- **Documento hermano:** [threat model (TT-702)](threat-model.md) — cubre el
  riesgo de **seguridad** (STRIDE). Esta EIPD cubre el riesgo para los
  **derechos y libertades** de las personas.
- **EIPD operativa:** [`eipd.md`](eipd.md) — la evaluación **decidible** para
  activar los dos trámites reales (lectura del documento con IA + reserva en
  portal real). Este documento es su **anexo técnico** (diseño y ciclo de vida
  del dato); la decisión de activación vive allí.

> Este es un **borrador técnico**, no la EIPD final. Describe el tratamiento tal
> como está implementado y evalúa los riesgos derivados del diseño. Las
> decisiones jurídicas —base de licitud, roles responsable/encargado, consulta
> previa a la AEPD, contratos de encargo— corresponden al DPD y a la asesoría
> jurídica y quedan marcadas como **[PENDIENTE JURÍDICO]**. El PRD §15.1 es
> explícito: no se presupone cumplimiento por diseño técnico.

---

## 1. Necesidad de la EIPD

Concurren varios de los criterios que obligan o recomiendan una EIPD (Art. 35.3
RGPD; lista de la AEPD; PRD §15.3):

- **Categorías especiales de datos** (Art. 9): datos de salud (cita de atención
  primaria, tarjeta SIP), documentos de identidad.
- **Población potencialmente vulnerable:** personas mayores o con baja
  competencia digital (el público objetivo del sistema).
- **Uso de inteligencia artificial** para tratar datos personales.
- **Tratamiento en espacio público** (tótem en sede institucional).
- **Posible observación/monitorización operativa** del uso.
- **Múltiples proveedores** (cloud, IA, soporte).
- **Uso de nuevas tecnologías** (visión, voz, navegación automatizada).

Conclusión: la EIPD es **obligatoria** antes de tratar documentos reales.

---

## 2. Descripción del tratamiento

### 2.1 Finalidad

Ayudar a una persona a **entender, preparar y completar** trámites
administrativos mediante un asistente multimodal en un tótem público. El sistema
**orienta y prepara; no decide ni resuelve** el trámite (PRD §6).

### 2.2 Naturaleza y ámbito

- Ámbito inicial: micro-piloto en Castilla y León (los dos trámites completos
  son la cita de atención primaria de Sacyl y la cita previa de la AEAT).
- **Anónimo por defecto:** sin cuentas, sin identificación del ciudadano, sin
  expediente ni memoria entre sesiones (PRD §6.1, §13.1).
- Operaciones: clasificación de la intención, orientación con fuentes oficiales,
  lectura de documentos/cartas, canal de voz, preparación asistida de citas.

### 2.3 Categorías de interesados

Cualquier persona que use el tótem. Especial atención a colectivos vulnerables
(mayores, baja competencia digital, posibles situaciones administrativas
sensibles: sanciones, embargos, extranjería).

### 2.4 Categorías de datos y clasificación (PRD §13.2)

| Nivel | Datos | Tratamiento en el sistema |
|---|---|---|
| A0 | intención, idioma, tipo de trámite | Podría agregarse como métrica anónima (no implementado hoy) |
| A1 | teléfono, correo, matrícula, código postal | Solo en sesión; nunca en log |
| A2 | DNI/NIE, SIP, fecha de nacimiento, nombre, **imágenes de documentos**, **audio de voz**, **contenido de cartas** (posibles datos de salud, económicos, judiciales) | Solo en sesión efímera o durante la petición; nunca persistido |
| A3 | certificados, Cl@ve, firma, credenciales | **Fuera del MVP**; el sistema no los trata ni automatiza |

Los datos de A2 incluyen **categorías especiales** (Art. 9): salud (SIP, cita
sanitaria), y potencialmente datos de una carta (p. ej. sanción, embargo).

---

## 3. Ciclo de vida del dato (dónde y cuánto vive)

Principio rector: **almacenamiento mínimo**. El sistema está diseñado para que
el dato personal viva lo menos posible.

```
Captura (cámara/micro/teclado, en el navegador)
   │  la imagen/audio se procesa y se descarta en la MISMA petición
   ▼
Sesión efímera (memoria o Redis con TTL nativo)
   │  identificador aleatorio, no vinculado a nombre ni documento
   │  TTL 20 min de inactividad (SESSION_TTL_SECONDS=1200)
   ▼
Purga: al pulsar "Terminar", por inactividad (aviso 90 s + cierre 30 s),
       o por expiración del TTL  →  Redis EXPIRE / borrado en memoria
   ▼
No queda nada: ni audio, ni texto libre, ni PII (E2E-01)
```

- **Sin base de datos de PII.** Documentos, cartas y datos extraídos viven
  dentro de la sesión (heredan su TTL y su purga); la voz y las imágenes no se
  escriben en ningún sitio (ADR-002, ADR-004, ADR-005).
- **Sin logs con PII.** El log de acceso registra método, ruta y estado; nunca
  cuerpos, query strings ni valores. Hay tests que fijan que valores centinela
  de DNI/teléfono/carta/audio no aparecen en logs (`test_privacy.py`).
- **Sin identificadores persistentes** del ciudadano: el id de sesión es
  aleatorio y desechable.
- **Datos persistentes permitidos** (PRD §13.3): solo metadatos operativos del
  parque de tótems (`kiosks`: id, municipio, versión, estado) — **sin PII**.

---

## 4. Necesidad y proporcionalidad

| Principio (Art. 5) | Cómo lo cumple el diseño |
|---|---|
| **Licitud** | [PENDIENTE JURÍDICO] Probable Art. 6.1.e (interés público/potestad pública del organismo) para A0/A1; para A2 con categorías especiales, base del Art. 9.2 (p. ej. 9.2.g interés público esencial, o 9.2.a consentimiento explícito por acción). A determinar por el DPD |
| **Limitación de la finalidad** | Cada trámite declara los campos que necesita (`required_fields`); el sistema no reutiliza los datos para otra cosa |
| **Minimización** | Solo se piden los campos del trámite; de los datos sensibles de una carta se informa del **tipo**, nunca del valor |
| **Exactitud** | Validadores deterministas + **revisión visual obligatoria** del ciudadano antes de usar cualquier dato extraído (ADR-002) |
| **Limitación del plazo** | Efímero: TTL de 20 min y purga; nada persiste entre sesiones |
| **Integridad y confidencialidad** | Ver threat model (TT-702): sin PII en logs, aislamiento entre sesiones, allowlist, degradación |
| **Responsabilidad proactiva** | ADRs que documentan cada decisión de datos; tests que fijan las garantías |

**Proporcionalidad:** la alternativa (retener datos, crear cuentas, automatizar
la resolución) sería más intrusiva. El diseño anónimo-efímero es la opción menos
lesiva compatible con la finalidad.

---

## 5. Decisiones automatizadas (Art. 22)

**El sistema no toma decisiones con efectos jurídicos ni significativos sobre la
persona.** Orienta y prepara; la persona confirma y ejecuta:

- La IA **explica**; el sistema **valida** con reglas deterministas (PRD §6.3).
- En cartas, el riesgo y los plazos son deterministas; el modelo solo transcribe
  (ADR-004); ante duda, escala a atención humana, no resuelve.
- La navegación asistida tiene **dos desenlaces** (decisión de producto
  2026-07-23): en trámites con Cl@ve/firma, **prepara y cede** (el worker nunca
  envía); en **citas reversibles sin Cl@ve** (médico, Hacienda), el worker
  **completa la reserva**, pero SOLO tras el "Sí, confirma" explícito del
  ciudadano en pantalla, y nunca automatiza CAPTCHA, Cl@ve ni firma (regla 5).
  Ver la EIPD operativa [`eipd.md`](eipd.md), que evalúa este tratamiento.

Reservar una cita es un acto **reversible y sin efecto jurídico** que la persona
**confirma expresamente**; no es una decisión únicamente automatizada del Art.
22. **[PENDIENTE JURÍDICO]** confirmarlo.

---

## 6. Destinatarios y transferencias

| Destinatario | Datos | Estado |
|---|---|---|
| Proveedor cloud (backend, región UE — Render/Frankfurt) | Sesión efímera (A1/A2 en tránsito y en memoria) | [PENDIENTE JURÍDICO] contrato de encargado |
| Proveedor de IA (Anthropic) | **A2 (imágenes DNI/SIP, cartas)** solo si se activa | **Desactivado por defecto** (doble interruptor, ADR-006); activarlo exige EIPD + §10.4 |
| Portales oficiales (Sacyl, AEAT…) | Los datos de la persona para reservar su cita (CIP+apellido o NIF+nombre, y las selecciones de centro/oficina/fecha) | Portales reales **desactivados** (`enabled=False`) hasta EIPD; hoy solo réplicas locales de pruebas (ADR-007) |
| Soporte/MDM | Metadatos de tótem (sin PII) | [PENDIENTE JURÍDICO] |

**Transferencias internacionales (Art. 44+):** el envío de A2 a un proveedor de
IA es el punto crítico. Antes de habilitarlo hay que verificar (PRD §10.4):
región de procesamiento, contrato de encargado/subencargado, **no uso para
entrenamiento**, retención, cifrado, borrado, transferencias internacionales,
certificaciones, desactivación de logs. **Hoy no ocurre ninguna transferencia de
A2 a un tercero.**

---

## 7. Derechos de los interesados

El diseño anónimo tiene una consecuencia favorable: **al no retener datos ni
crear identificadores, la mayoría de los derechos quedan satisfechos
estructuralmente**.

| Derecho | Situación |
|---|---|
| Información (Art. 13) | Debe mostrarse en el tótem: quién trata, para qué, base, derechos. **[PENDIENTE]** cartel/aviso de privacidad accesible y bilingüe |
| Acceso, rectificación, supresión, portabilidad | No hay dato retenido tras la sesión ni cuenta que consultar: no hay nada que acceder/suprimir después. Durante la sesión, la persona revisa y puede borrar (voz, carta, documento) |
| Oposición / limitación | La voz y los flujos de documento son opcionales y desactivables |
| No ser objeto de decisiones automatizadas | Ver §5 |

**[PENDIENTE]** redactar el **aviso de privacidad** para la pantalla y la
cartelería del tótem (información del Art. 13), bilingüe y en lenguaje claro.

---

## 8. Evaluación de riesgos para derechos y libertades

Escala: Probabilidad (Baja/Media/Alta) × Impacto (Bajo/Medio/Alto/Muy alto).

| # | Riesgo para la persona | Prob. | Impacto | Medidas implementadas | Residual |
|---|---|---|---|---|---|
| P1 | Que sus datos queden accesibles al siguiente usuario del tótem | Media | Alto | Sesión efímera + purga + aislamiento (E2E-05); guardia de inactividad; botón de borrado | **Bajo-Medio** — pendiente verificar purga de cachés del navegador del tótem (TT-203) |
| P2 | Que sus datos sensibles se filtren a un tercero (IA) sin base | Baja | Muy alto | Doble interruptor apagado por defecto (ADR-006); sin clave nada sale | **Bajo hoy** — **Alto si se activa sin completar §10.4/EIPD** |
| P3 | Que la IA se invente un requisito o un plazo y le perjudique | Media | Alto | RAG extractivo con cita de fuente (ADR-003); en cartas, plazos/riesgo deterministas (ADR-004); nunca consejo jurídico | **Bajo-Medio** |
| P4 | Que se exponga el valor de un dato sensible en pantalla/voz | Baja | Alto | Se informa del tipo, no del valor; tests lo fijan | **Bajo** |
| P5 | Shoulder surfing / escucha en espacio público | Media | Medio-Alto | Diseño de pantalla; voz desactivable; **[PENDIENTE hardware]** auricular/mampara (§14.4) | **Medio** |
| P6 | Que una persona vulnerable crea que el sistema "decide" su trámite | Media | Alto | Mensajes de que prepara y cede; deriva a humano en casos de alto impacto | **Bajo-Medio** |
| P7 | Que se retenga PII por error (log, caché, base de datos) | Baja | Muy alto | No hay almacén de PII; tests de privacidad; efímero por diseño | **Bajo** |
| P8 | Perfilado/monitorización del uso individual | Baja | Alto | Sin expediente ni id persistente; solo posibles métricas A0 agregadas | **Bajo** |
| P9 | Acceso remoto silencioso a una sesión ciudadana (soporte) | Baja | Muy alto | Prohibido por política (§15.4) | **Medio** — pendiente de la política de soporte/MDM |

---

## 9. Riesgo residual y medidas pendientes (priorizadas)

| Prioridad | Medida | Responsable |
|---|---|---|
| **Bloqueante** | No activar el envío de A2 a Anthropic hasta completar §10.4 + esta EIPD | DPD + técnica |
| **Alta** | Aviso de privacidad (Art. 13) en el tótem, bilingüe y accesible | Jurídica + diseño |
| **Alta** | Determinar la base de licitud (Art. 6/9) y los roles responsable/encargado | DPD + jurídica |
| **Alta** | Verificar purga de cachés/almacenamiento del navegador del tótem (TT-203) | Técnica |
| Media | Política de soporte sin acceso silencioso a sesiones (P9) | Operación |
| Media | Privacidad acústica/visual del tótem (P5) | Hardware/espacio |
| Media | Cerrar el threat model (TT-702): rate limiting, auth device-agent, infra §15.4 | Técnica |
| — | Valorar consulta previa a la AEPD si el riesgo residual sigue alto (Art. 36) | DPD |

---

## 10. Conclusión (borrador)

El diseño **minimiza el riesgo por construcción**: anónimo, efímero, sin
persistencia de PII, sin decisiones automatizadas con efectos jurídicos, y con
el envío de datos sensibles a terceros **apagado por defecto**. Las garantías
técnicas están implementadas y cubiertas por tests.

El riesgo residual relevante es **jurídico y de despliegue**, no de diseño de
datos: base de licitud, aviso de privacidad, contratos de encargo, endurecimiento
del tótem y —sobre todo— la decisión de si se habilita el proveedor de IA para
datos A2, que **no debe tomarse sin cerrar esta EIPD**.

Este borrador debe ser revisado y completado por el DPD y la asesoría jurídica
antes del micro-piloto.

---

## 11. Control de versiones

Cada ADR o cambio que afecte a categorías de datos, destinatarios, plazos de
conservación o decisiones automatizadas debe actualizar esta EIPD y el threat
model. Versión inicial: borrador técnico 2026-07-21.

# EIPD — Activación de trámites reales en Tramitatrón (BORRADOR)

> **Evaluación de Impacto relativa a la Protección de Datos (Art. 35 RGPD).**
> Documento **decidible**: su objeto es que el responsable del tratamiento,
> asistido por su Delegado de Protección de Datos (DPD), decida si activa —y bajo
> qué condiciones— los dos trámites que tratan datos personales reales.

| Campo | Valor |
|---|---|
| **Estado** | **BORRADOR** para revisión y firma del DPD y la asesoría jurídica del responsable |
| **Versión / fecha** | 0.1 · 2026-07-24 |
| **Preparado por** | El proveedor del sistema (encargado del tratamiento), como apoyo al responsable |
| **Base metodológica** | Art. 35.7 RGPD; guía de la AEPD «Gestión del riesgo y evaluación de impacto en tratamientos de datos personales»; LOPDGDD (LO 3/2018) |
| **Documentos relacionados** | [`eipd-tecnica.md`](eipd-tecnica.md) (diseño y ciclo de vida del dato) · [`threat-model.md`](threat-model.md) (seguridad, STRIDE) · [`activacion-opcion-3.md`](activacion-opcion-3.md) (runbook de activación) |

> **Aviso.** Esto es un borrador técnico-organizativo, **no asesoramiento
> jurídico**. La EIPD es una obligación del **responsable** (la administración
> que despliega el tótem), que la valida y firma a través de su DPD. Las
> casillas **[A DECIDIR POR EL DPD]** marcan lo que corresponde a la entidad. El
> proveedor aporta este borrador porque conoce el tratamiento por diseño.

---

## 1. Objeto y alcance

Hoy Tramitatrón funciona de punta a punta pero **no toca ninguna administración
real**: la lectura de documentos es sintética y los portales son réplicas
locales de pruebas. Esta EIPD evalúa el paso a **producción real** de los dos
trámites completos:

- **T1 — Pedir cita con el médico** (atención primaria, Sacyl). Identificación
  con el **CIP** de la tarjeta sanitaria + primer apellido. **Sin Cl@ve.**
- **T2 — Pedir cita en Hacienda** (cita previa, AEAT). Identificación con
  **NIF + nombre y apellidos**. **Sin Cl@ve** (la propia AEAT confirma que para
  pedir cita no hacen falta certificado, DNIe ni Cl@ve).

Poner estos trámites en real implica activar **dos tratamientos** hoy apagados,
que se evalúan por separado porque tienen riesgos distintos y pueden habilitarse
de forma independiente:

- **Activación A — Lectura del documento con IA** (opción 3): la imagen del DNI
  o de la tarjeta sanitaria se envía a un proveedor de IA (visión) para extraer
  los datos, en lugar del mock actual. *Es lo que evita que la persona teclee.*
- **Activación B — Navegación y reserva en el portal real**: conducir el portal
  oficial (Sacyl/AEAT) hasta reservar la cita, en lugar de la réplica local.

---

## 2. ¿Es obligatoria la EIPD?

Concurren varios criterios del Art. 35.3 RGPD y de la lista de la AEPD (basta con
dos): **categorías especiales de datos** (salud, en T1), **uso innovador de
tecnología** (IA de visión sobre documentos), **datos de colectivos
vulnerables** (personas mayores y con baja competencia digital, que son el
público objetivo), **tratamiento a escala** (parque de tótems) y **transferencia
internacional** (si el proveedor de IA está fuera del EEE). 

**Conclusión: la EIPD es obligatoria** antes de tratar documentos reales o de
apuntar la navegación a un portal real. **[A DECIDIR POR EL DPD]** confirmarlo.

---

## 3. Descripción sistemática del tratamiento

### 3.1 Roles

| Rol | Quién | Notas |
|---|---|---|
| **Responsable** | La administración que despliega el tótem (ayuntamiento, diputación o Junta) | Titular de la decisión y de esta EIPD. **[A COMPLETAR]** |
| **Encargado** | El proveedor de Tramitatrón | Trata por cuenta del responsable; contrato de encargo del Art. 28 **[PENDIENTE]** |
| **Subencargado** | Proveedor de IA (Anthropic), **solo si se activa A** | Requiere DPA y garantías de transferencia. **Hoy desactivado** |
| **Terceros receptores** | Portales oficiales (Sacyl / AEAT), **solo si se activa B** | Son responsables de su propio tratamiento cuando reciben la solicitud de cita |

### 3.2 Fines y encaje jurídico (propuesta)

Fin: **asistir** a la persona a realizar su trámite en un canal accesible, sin
sustituir su identificación ni su firma. Es la asistencia en el uso de medios
electrónicos del **art. 12 de la Ley 39/2015** — una obligación de la propia
administración, que aquí sirve de norma habilitante en Derecho interno (art. 6.3
RGPD).

| Tratamiento | Base de licitud propuesta (**[A DECIDIR POR EL DPD]**) |
|---|---|
| General (datos identificativos, selecciones del trámite) | **Art. 6.1.e** RGPD — misión de interés público / ejercicio de poderes públicos, con habilitación en el art. 12 Ley 39/2015 |
| Lectura del documento con IA (activación A) | **Consentimiento explícito** de la persona en pantalla (**art. 6.1.a**), por ser un canal **voluntario** con alternativa humana equivalente; revocable en cualquier momento |
| Datos de salud de la cita médica T1 (CIP + solicitud de asistencia primaria) | **Categoría especial (art. 9).** Base propuesta: **art. 9.2.a** (consentimiento explícito recabado en pantalla). Alternativas a valorar: 9.2.g (interés público esencial) o 9.2.h (gestión de servicios de asistencia sanitaria) |

**Art. 22 (decisiones automatizadas):** reservar una cita es un acto
**reversible, anulable y sin efecto jurídico**, que además la persona
**confirma expresamente** ("Sí, confirma mi cita") antes de que se envíe. No es
una decisión únicamente automatizada. **[A DECIDIR POR EL DPD]** confirmarlo.

### 3.3 Categorías de interesados y de datos

Interesados: cualquier persona que use el tótem; especial atención a personas
mayores y con baja competencia digital.

| Trámite | Datos que se tratan | Origen | ¿Categoría especial? |
|---|---|---|---|
| **T1 médico** | Nº de tarjeta sanitaria (CIP), primer apellido; centro, día, hora | Escaneo de la tarjeta (A) + selección | **Sí** — dato relativo a la salud (art. 9) |
| **T2 Hacienda** | NIF, nombre y apellidos; gestión, oficina, día, hora | Escaneo del DNI (A) + selección | No (dato identificativo/tributario) |
| Imagen del documento | Fotograma del DNI o la tarjeta durante la lectura | Cámara del tótem | Contiene la fotografía; **no se hace tratamiento biométrico** (solo OCR de texto) |

### 3.4 Flujos de datos de las dos activaciones

**Activación A — lectura del documento con IA:**

```
Cámara del tótem (imagen del documento, en el navegador)
   │  solo el fotograma que la persona decide usar; nunca vídeo ni la escena
   ▼
API (en sesión efímera)  ──►  Proveedor de IA (visión)   [SUBENCARGADO / posible transferencia internacional]
   │                             devuelve los campos (CIP/NIF, nombre, apellido)
   │  la imagen NO se persiste; se descarta tras la petición
   ▼
Revisión VISUAL obligatoria de la persona en pantalla (puede corregir)
```

**Activación B — navegación y reserva en el portal real:**

```
Datos revisados (del documento) + selecciones (centro/oficina/fecha/hora)
   ▼
Navegación asistida del portal oficial (allowlist estricta de hosts + esquema)
   │  rellena los campos; valida el destino ANTES de cada salto y del envío
   ▼
Resumen en pantalla → "Sí, confirma mi cita"  (confirmación explícita)
   ▼
Reserva  →  el portal devuelve la referencia de la cita  →  se imprime
   │  los eventos registran NOMBRES de campo, jamás valores (PII)
   ▼
Fin de sesión: purga. No queda imagen, ni valores, ni identificador de la persona.
```

Ciclo de vida detallado (efímero, sin persistencia de PII): ver
[`eipd-tecnica.md`](eipd-tecnica.md) §3.

### 3.5 Destinatarios y transferencias internacionales

| Destinatario | Datos | Activación | Punto crítico |
|---|---|---|---|
| Proveedor de IA (Anthropic) | Imagen del documento + campos extraídos | **A** | **Posible transferencia fuera del EEE (Art. 44+).** Exige mecanismo válido de transferencia (cláusulas tipo/adecuación), DPA con **no uso para entrenamiento**, **retención cero**, logs desactivados y región adecuada |
| Portal oficial (Sacyl / AEAT) | Datos mínimos para reservar la cita | **B** | Cesión a la administración competente para dar la cita; verificar términos de uso y permiso del organismo |

---

## 4. Necesidad y proporcionalidad

- **Idoneidad:** el tótem cumple la finalidad (asistir a quien no es autónomo
  digitalmente) mejor que la web (que exige destreza) y con más horario/cobertura
  que la ventanilla, especialmente en el medio rural.
- **Necesidad (alternativa menos intrusiva):** existe siempre el personal humano;
  el tótem **no lo sustituye, lo complementa**, y es de uso **voluntario**. La
  lectura con IA (A) evita teclear datos sensibles en una máquina pública, lo que
  reduce el error y el *shoulder surfing*.
- **Proporcionalidad estricta y minimización específica:**
  - Se tratan **solo** los datos que el trámite necesita (`required_fields` +
    selecciones); nada más.
  - **No se usa Cl@ve, certificado ni firma** (no hacen falta para estas citas):
    se elimina de raíz el dato más sensible.
  - A la IA se le envía **solo la imagen del documento** que la persona elige,
    nunca vídeo ni la escena, y **no se conserva**.
  - **Anónimo y efímero:** sin cuentas, sin expediente, sin memoria entre
    sesiones; el id de sesión es aleatorio y desechable.
  - De un dato sensible se informa del **tipo**, nunca del valor; los **logs y
    eventos no contienen valores** (hay tests que lo fijan).

**Derechos de los interesados (Art. 13-22):** al no retener datos ni crear
identificadores, acceso/rectificación/supresión quedan satisfechos
estructuralmente tras la sesión. Pendiente **[ALTA]**: el **aviso de privacidad
del art. 13** en pantalla y cartelería, bilingüe y accesible, y la **recogida en
pantalla del consentimiento explícito** (para la base 6.1.a / 9.2.a de la
activación A).

---

## 5. Análisis de riesgos de las dos activaciones

Riesgos **específicos** de pasar a real (los riesgos generales del diseño están
en [`eipd-tecnica.md`](eipd-tecnica.md) §8). Escala: Probabilidad × Impacto.

| # | Riesgo para la persona | Prob. | Impacto | Activación |
|---|---|---|---|---|
| RA1 | La IA lee mal el documento y se reserva con datos erróneos | Media | Medio | A |
| RA2 | La imagen del documento se transfiere a un tercero fuera del EEE sin garantías suficientes | Media | **Muy alto** | A |
| RA3 | El proveedor de IA conserva o usa la imagen para entrenar | Baja | **Muy alto** | A |
| RB1 | Se reserva una cita no querida o a nombre equivocado | Baja | Medio | B |
| RB2 | Alguien usa el documento de otra persona (suplantación) | Baja | Alto | A+B |
| RB3 | El CIP / NIF se expone en tránsito o en el portal | Baja | Alto | B |
| RB4 | El portal cambia y la automatización hace algo inesperado | Media | Medio | B |
| RC1 | Exposición de un dato de salud (que la persona pide cita médica) | Baja | Alto | A+B (T1) |

---

## 6. Medidas para afrontar los riesgos

**Ya implementadas y verificadas** (cubren el diseño y parte de cada riesgo):

| Medida | Riesgos que mitiga |
|---|---|
| **Revisión visual obligatoria** del dato leído antes de usarlo; la persona corrige | RA1, RB2 |
| **Confirmación explícita** antes de reservar ("Sí, confirma"); sin ella, la API responde 400 y el portal 403 (doble garantía) | RB1 |
| **Nunca** se automatiza CAPTCHA, Cl@ve ni firma (regla 5) | RB2 |
| **Allowlist estricta** de hosts + **mismo esquema** (sin downgrade a http, sin `javascript:`/`file:`); se valida también el **destino del POST** antes de enviar | RB3, RB4 |
| **Gateway de IA apagado por defecto** (`ANTHROPIC_ALLOW_DOCUMENTS=false`); sin clave, nada sale de la máquina | RA2, RA3 |
| **Minimización a la IA**: solo la imagen del documento elegido; degradación a confianza 0 ante fallo/`refusal`; **no se registran** valores ni el texto | RA1, RA3, RC1 |
| **Anónimo y efímero**; **sin PII en logs/eventos** (nombres de campo, no valores); higiene del spool de impresión | RB3, RC1 |
| **Healthcheck sintético** del portal (TT-505): detecta si el formulario cambió | RB4 |
| **Forma de la petición a la IA fijada por tests** para detectar deriva de la API antes de activar | RA1 |

**Pendientes — condiciones de activación** (no son código; son la puerta):

| Prioridad | Medida | Activación |
|---|---|---|
| **Bloqueante** | **DPA con el proveedor de IA**: mecanismo de transferencia válido (cláusulas tipo/adecuación), **no entrenamiento**, **retención cero**, logs off, región adecuada | A |
| **Bloqueante** | **Permiso/validación del organismo** titular del portal (Sacyl/AEAT) y revisión de sus términos de uso | B |
| **Alta** | **Aviso de privacidad (art. 13)** en pantalla + cartelería, bilingüe y accesible, y **recogida del consentimiento explícito** para A | A, B |
| **Alta** | Confirmar y mostrar **cómo anular** la cita (refuerza que es reversible) | B |
| **Alta** | Arquitectura **"navegador visible del propio tótem con la persona delante"** (asistencia del art. 12, más defendible y menos expuesta a detección de bots) en lugar del worker headless para el portal real | B |
| Media | Privacidad acústica/visual del tótem (mampara/auricular) | A, B |
| Media | Definir base de licitud definitiva y roles responsable/encargado; contrato de encargo (art. 28) | A, B |

---

## 7. Riesgo residual y consulta previa (Art. 36)

Con las medidas **implementadas**, el riesgo del diseño es **bajo**. El riesgo
residual relevante se concentra en la **activación A** (transferencia de la
imagen del documento a un proveedor de IA): si no se cierran las garantías del
DPA y de la transferencia internacional, el residual es **alto** y **no debe
activarse**.

**[A DECIDIR POR EL DPD]** Si tras las medidas el riesgo residual sigue siendo
**alto** —caso plausible para la activación A con transferencia fuera del EEE—,
procede **consulta previa a la AEPD (art. 36)** antes de activar. La activación B
(portal real, sin IA) tiene un residual menor y no requeriría, en principio,
consulta previa.

---

## 8. Condiciones de activación (checklist decidible)

Las dos activaciones son **independientes**. Se puede, por ejemplo, activar B
(portal real con lectura aún sintética) sin activar A, o al revés. El runbook
técnico está en [`activacion-opcion-3.md`](activacion-opcion-3.md).

**Activación A — lectura del documento con IA:**
- [ ] EIPD aprobada por el DPD y (si aplica) consulta previa a la AEPD resuelta
- [ ] DPA firmado con el proveedor de IA: transferencia válida, no entrenamiento, retención cero, logs off, región
- [ ] Aviso de privacidad (art. 13) y recogida de consentimiento explícito en pantalla
- [ ] `ANTHROPIC_API_KEY` en `.env` + `ANTHROPIC_ALLOW_DOCUMENTS=true` + reinicio
- [ ] Prueba de humo y verificación de que no aparece PII en logs
- **Rollback:** `ANTHROPIC_ALLOW_DOCUMENTS=false` + reinicio

**Activación B — portal real (por trámite):**
- [ ] EIPD aprobada por el DPD para ese trámite
- [ ] Permiso/validación del organismo titular del portal y revisión de términos
- [ ] Arquitectura de navegación asistida en el tótem (persona presente) lista
- [ ] `PortalSpec.enabled = True` para ese conector (Sacyl / AEAT)
- [ ] Verificado el flujo real hasta reservar y anular una cita de prueba
- **Rollback:** `enabled = False` para ese conector

---

## 9. Decisión (a cumplimentar y firmar por el responsable)

> **[A DECIDIR POR EL DPD / RESPONSABLE]**

- Activación A (lectura con IA): [ ] No activar · [ ] Activar con las condiciones del §8 · [ ] Elevar consulta previa a la AEPD
- Activación B (portal real T1 médico): [ ] No activar · [ ] Activar con las condiciones del §8
- Activación B (portal real T2 Hacienda): [ ] No activar · [ ] Activar con las condiciones del §8

Condiciones/observaciones: __________________________________________

| | Nombre | Fecha | Firma |
|---|---|---|---|
| **DPD** | | | |
| **Responsable del tratamiento** | | | |

---

## Anexo I — Registro de Actividades del Tratamiento (RAT, Art. 30) · plantilla

| Campo | Contenido propuesto (**[A VALIDAR]**) |
|---|---|
| Nombre del tratamiento | Asistencia a la ciudadanía en trámites mediante tótem (Tramitatrón) |
| Responsable | La administración que despliega **[A COMPLETAR]** |
| Encargado | Proveedor de Tramitatrón (contrato art. 28) |
| Fines | Asistencia en el uso de medios electrónicos (art. 12 Ley 39/2015): preparar y reservar citas |
| Base jurídica | 6.1.e + art. 12 Ley 39/2015; consentimiento explícito (6.1.a / 9.2.a) para la lectura con IA y los datos de salud |
| Categorías de interesados | Personas usuarias del tótem |
| Categorías de datos | Identificativos (NIF/CIP, nombre, apellido); salud (solicitud de cita de atención primaria); selecciones del trámite |
| Categorías especiales | Salud (art. 9), en la cita médica |
| Destinatarios | Portales de la administración competente (Sacyl/AEAT); proveedor de IA (subencargado, solo activación A) |
| Transferencias internacionales | Solo si se activa A: proveedor de IA — mecanismo **[A DETERMINAR]** |
| Plazos de supresión | Efímero: TTL de sesión (~20 min) y purga; sin persistencia de PII |
| Medidas de seguridad | Ver [`threat-model.md`](threat-model.md) y §6 de esta EIPD |

---

## Control de versiones

- **0.1 · 2026-07-24** — Versión inicial. Cubre la activación de los dos
  trámites reales (T1 Sacyl, T2 AEAT) y las dos activaciones (A: lectura con IA;
  B: portal real). Complementa la EIPD técnica y el threat model.

Cualquier cambio en categorías de datos, destinatarios, plazos o en el modelo de
"completar" debe actualizar esta EIPD, la EIPD técnica y el threat model.

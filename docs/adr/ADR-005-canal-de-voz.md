# ADR-005 — Canal de voz: nada persiste y la síntesis es local

- **Estado:** aceptado
- **Fecha:** 2026-07-18
- **Contexto:** PRD §14.3 (voz), §13.2 (datos prohibidos), §10.1 (gateway), E2E-01

## Contexto

El PRD pide que el ciudadano pueda "decir qué necesita con su propia voz"
(§5.1) con ocho requisitos concretos (§14.3) y, a la vez, prohíbe persistir
**audio bruto** (§13.2) y exige que al cerrar la sesión "no quede audio, texto
libre ni PII" (E2E-01).

## Decisiones

### 1. La transcripción no se guarda en ninguna parte

A diferencia de documentos y cartas —que sí viven en la sesión con su TTL—,
el endpoint `/api/session/{id}/voice/transcribe` **no escribe nada**. El audio
se decodifica, se transcribe y se descarta dentro de la misma petición; el
texto viaja en la respuesta y vive solo en la memoria del navegador hasta que
la persona lo confirma o lo borra.

La forma más sencilla de garantizar que no queda audio ni texto libre es no
escribirlos nunca. Hay tests que fijan que `data_keys` sigue vacío tras
transcribir y que ni el audio ni el texto aparecen en los logs.

### 2. La voz nunca actúa sola

La transcripción se **muestra** y requiere confirmación explícita antes de
usarse (§14.3). Si la confianza baja de 0,60 el campo `usable` llega en falso
y la interfaz **oculta el botón de confirmar**: solo ofrece repetir o borrar.
Actuar sobre un "no sé… una cosa del…" mal entendido es peor que no hacer nada.

La voz acompaña al buscador de texto; no lo sustituye. Se puede desactivar
desde la cabecera, junto al tamaño de letra y el alto contraste.

### 3. Pulsar y soltar, no mantener pulsado

El PRD dice "pulsar para hablar". Lo implementamos como pulsar para empezar y
volver a pulsar para parar, en vez de mantener el dedo apretado: sostener un
botón es difícil con temblor, artritis o poca fuerza, justo en el público
objetivo. Hay un corte automático a los 20 segundos para que un micrófono
olvidado no siga capturando la sala.

### 4. La síntesis de voz es LOCAL, fuera del gateway

**Esta es una desviación consciente del PRD §10.1**, que lista `synthesize`
como método del `ModelGateway`.

La lectura en voz alta usa `SpeechSynthesis` del navegador. Motivo: lo que hay
que leer en alto incluye el contenido de cartas administrativas y datos del
ciudadano. Mandar ese texto a un proveedor de TTS para convertirlo en audio
sería enviar a un tercero exactamente los datos que el PRD §13.2 protege, y a
cambio de nada: la síntesis local funciona sin red, sin latencia y sin coste.

`transcribe` **sí** está en el gateway, porque el reconocimiento de voz sí
necesita un modelo y debe poder cambiarse de proveedor.

Si en el futuro se quiere una voz de más calidad, la decisión debe revisarse
junto con la política de proveedores del PRD §10.4, no antes.

## Estado actual

`MockModelGateway.transcribe` devuelve frases sintéticas: **no hay
reconocimiento de voz real** hasta que exista un proveedor. Todo lo demás
—grabación, indicador, revisión, confirmación, borrado, desactivación y
lectura en voz alta— ya es real y funciona. Al conectar un STT solo cambia el
texto que devuelve el gateway.

## Pendiente

- Auricular o altavoz direccional (§14.3) y privacidad acústica: es una
  decisión de hardware del tótem, no de software.
- Control de volumen (§14.2): hoy depende del volumen del sistema.

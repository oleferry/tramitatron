# ADR-004 — Explicación de cartas: la IA transcribe, las reglas deciden

- **Estado:** aceptado
- **Fecha:** 2026-07-18
- **Contexto:** TT-404, PRD §5.2 caso D, E2E-04

## Contexto

El caso D del PRD permite a un ciudadano fotografiar una carta administrativa
para que el sistema se la explique. Es el flujo con más riesgo del MVP: quien
llega con una carta de embargo suele ser exactamente la persona con menos
recursos para interpretarla, y una explicación equivocada puede hacer que
pierda un plazo o que no busque ayuda.

La tentación es resolverlo entero con un modelo de lenguaje: leer la imagen,
resumir y clasificar la gravedad de una sola pasada.

## Decisión

Separamos el flujo en dos mitades con responsabilidades distintas:

1. **El modelo solo transcribe.** `explain_official_content` (contrato del
   gateway, PRD §10.1) devuelve el texto leído, el organismo si lo distingue y
   una confianza. No interpreta, no resume y no valora la gravedad.
2. **Las reglas deciden.** `app/letters/analysis.py` clasifica el riesgo,
   detecta plazos y detecta datos sensibles con expresiones regulares
   auditables. `app/letters/wording.py` redacta con plantillas fijas
   bilingües.

Consecuencias concretas:

- Una alucinación **no puede** rebajar el riesgo de un embargo: la palabra
  "embargo" en el texto activa la derivación a atención humana, pase lo que
  pase por la cabeza del modelo.
- Los plazos solo se muestran cuando aparecen de forma inequívoca ("plazo de
  un mes", "antes del 30/09/2026"). Un "a la mayor brevedad" **no** es un
  plazo: se marca como ambiguo y eso, por sí solo, deriva a una persona
  (el PRD incluye "plazos dudosos" como motivo de derivación).
- Si la transcripción viene con confianza < 0.55 no se interpreta nada: se
  pide repetir la foto. **Explicar mal una carta es peor que admitir que no se
  ha podido leer.**
- La respuesta separa `facts` (lo que pone el documento) de `explanation` (la
  lectura del sistema), y la interfaz los muestra en bloques distintos, como
  exige el PRD §5.2.
- Nunca se sugiere una actuación jurídica concreta. Los textos de
  `wording.py` avisan y derivan; no dicen cómo recurrir ni si conviene hacerlo.

## Privacidad

- La imagen vive solo durante la petición. No se escribe en disco ni en logs.
- El análisis se guarda como una clave más de la sesión (`letter_<id>`), así
  que hereda su TTL y su purga; no hay ningún almacén de cartas.
- De los datos sensibles se informa **del tipo, nunca del valor**: la respuesta
  dice "contiene tu DNI", no el número. Hay tests que fijan esto.
- La pantalla borra la carta explícitamente al salir o al leer otra, sin
  esperar al fin de la sesión.

## Alternativas descartadas

- **Un único modelo que lea, resuma y clasifique el riesgo.** Más simple y
  produce mejor prosa, pero hace que la seguridad del ciudadano dependa de una
  generación no determinista e irreproducible. Descartado.
- **Resumen generativo sobre reglas de riesgo.** Mantendría la garantía de
  seguridad, pero el texto dejaría de ser auditable y podría contradecir a los
  hechos detectados. Se revisará cuando exista un gateway real, con los
  hechos ya calculados como contexto de entrada.

## Estado actual

`MockModelGateway.explain_official_content` devuelve cartas sintéticas: **no
hay OCR real** hasta que exista un `ModelGateway` con modelo de visión. Toda
la mitad determinista (riesgo, plazos, datos sensibles, redacción) ya es real
y está cubierta por tests; al conectar un proveedor solo cambia la
transcripción.

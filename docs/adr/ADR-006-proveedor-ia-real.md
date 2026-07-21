# ADR-006 — Proveedor de IA real detrás del gateway, seguro por defecto

- **Estado:** aceptado
- **Fecha:** 2026-07-21
- **Contexto:** PRD §10 (gateway multimodelo), §10.4 (política de proveedores), §13.2 (clasificación de datos), regla 11 y 12 del §30

## Contexto

El gateway (`app/gateway/base.py`) abstrae al proveedor de IA para que la lógica
de negocio no dependa de ninguno (regla 11). Hasta ahora solo existía el mock.
Se pide conectar un proveedor real (Claude / Anthropic) para: clasificar la
intención del ciudadano, leer documentos (DNI/SIP), transcribir cartas y
transcribir voz.

Dos tensiones lo condicionan:

1. **Privacidad (§13.2).** Las imágenes de documentos y el contenido de las
   cartas son datos **A2**. El PRD dice que enviarlos a un proveedor externo
   "requerirá una decisión de arquitectura, base jurídica, registro de
   tratamiento y actualización de la EIPD". No es un simple flag técnico.
2. **Demo reproducible (regla 12).** El sistema debe seguir arrancando y
   funcionando en local sin ninguna clave ni servicio externo.

## Decisión

Se añade `AnthropicModelGateway` que implementa el contrato con Claude
(`claude-opus-4-8` por defecto, configurable), con estas reglas:

### 1. Mock por defecto; proveedor real solo con clave explícita

`_build_gateway` (en `main.py`) elige el mock salvo que exista
`ANTHROPIC_API_KEY`. Sin clave **no sale ningún dato de la máquina** y la demo
funciona igual. Añadir la clave es una acción deliberada del operador.

### 2. Los datos A2 van detrás de un SEGUNDO interruptor, apagado por defecto

Aunque haya proveedor real, la extracción de documentos
(`extract_document`) y el OCR de cartas (`explain_official_content`) **siguen
usando el mock** hasta que `ANTHROPIC_ALLOW_DOCUMENTS=true`. Este flag codifica
en el software la frontera del §13.2: enviar imágenes de DNI o el texto de una
carta a un tercero es la decisión que necesita EIPD, y no debe ocurrir por el
mero hecho de tener una clave. La clasificación de intención (texto que el
ciudadano escribe) sí usa el proveedor real cuando hay clave, por ser de menor
sensibilidad y necesaria para el buscador.

### 3. La voz nunca usa Claude

Claude no transcribe audio. `transcribe` delega siempre en el fallback, así que
**no sale audio** por esta vía. Integrar un STT real (Whisper, Deepgram…) es una
decisión de proveedor aparte, pendiente y sujeta al mismo §10.4.

### 4. Degradación sin inventar datos

Ante cualquier fallo del proveedor (red, `refusal`, rate limit):

- **Intención** → cae al mock determinista por palabras clave; el buscador no se
  cae nunca.
- **Documentos** → campos vacíos con confianza 0, para que el kiosco marque
  revisión y pida repetir la foto. **Nunca** datos sintéticos presentados como
  reales.
- **Cartas** → transcripción vacía y confianza 0, que el explicador ya trata
  como "no se ha podido leer, repite" (ADR-004).

### 5. Sin registro de PII

El gateway no escribe jamás los valores extraídos ni el texto de las cartas en
logs. Los tests de privacidad existentes siguen aplicando.

## Política de proveedores pendiente (§10.4)

Activar `ANTHROPIC_ALLOW_DOCUMENTS` en un piloto real exige, antes, verificar y
documentar: región de procesamiento (UE), contrato de encargado/subencargado,
retención, **no uso para entrenamiento**, cifrado, borrado, transferencias
internacionales, certificaciones, desactivación de logs del proveedor y
compatibilidad con ENS. Esta ADR habilita la palanca técnica; **no** sustituye
esa verificación jurídica.

## Estado y prueba

- El `anthropic` SDK es un extra opcional (`pip install -e ".[ai]"`).
- La selección de gateway, el gateo de documentos, la degradación y el que la
  voz nunca use el proveedor están cubiertos por tests con un cliente falso
  (`tests/test_gateway_anthropic.py`), sin red.
- El camino con **llamadas reales a Claude** no se ha podido ejercitar en el
  entorno de desarrollo (sin clave). Al añadir `ANTHROPIC_API_KEY` hay que
  validar de extremo a extremo el clasificador de intención antes de confiar en
  él, y superar la política del §10.4 antes de encender los documentos.

## Alternativas descartadas

- **Activar el proveedor real y los documentos con solo la clave.** Más directo,
  pero enviaría imágenes de DNI a un tercero sin la decisión de EIPD que el PRD
  exige. Descartado.
- **Reemplazar el mock.** Rompería la demo local sin clave (regla 12). El mock
  se mantiene como fallback permanente.

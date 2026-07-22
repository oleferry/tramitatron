# Runbook de activación — Opción 3: lectura real de documentos con IA

> Estado: **PREPARADO, DESACTIVADO.** Todo el código está escrito y probado con
> cliente simulado; falta la decisión legal (EIPD) y el interruptor. Activarlo
> es cambiar configuración, no escribir código.

## Qué activa

Hoy la extracción de DNI/SIP y el OCR de cartas son **sintéticos** (el
`MockModelGateway` ignora la imagen). La opción 3 enruta esas imágenes al
proveedor de IA real (Claude, visión) a través de `AnthropicModelGateway`
(`app/gateway/anthropic_gateway.py`), que ya está implementado y cumple:

- solo pide los campos declarados por clase de documento;
- la carta **solo se transcribe**, nunca se resume ni se valora (ADR-004);
- ante fallo o `refusal`, degrada a confianza 0 (el kiosco pide repetir),
  nunca datos sintéticos presentados como reales;
- no registra jamás los valores extraídos ni el texto de las cartas.

Estos comportamientos están fijados por tests (`test_gateway_anthropic.py`),
incluida la **forma exacta de la petición** a la API (visión base64 +
structured outputs), para detectar cualquier deriva de la API antes de activar.

## Puerta que hay que cruzar ANTES de activar (no técnica)

Enviar imágenes de DNI/SIP y cartas (datos **A2**, PRD §13.2) a un proveedor
externo requiere, según el PRD §10.4 y ADR-006:

1. **EIPD actualizada** que cubra este tratamiento (transferencia de A2 a la IA):
   finalidad, minimización, base jurídica, riesgos y medidas.
2. **Base jurídica** del tratamiento documentada.
3. **Encargo de tratamiento (DPA)** firmado con el proveedor (Anthropic),
   con garantías de no-entrenamiento y de ubicación/retención de datos.
4. **Registro de actividades de tratamiento** actualizado.
5. Revisión de que la política de **retención cero / no entrenamiento** del
   proveedor está contratada para la clave que se use.

Sin esto, `ANTHROPIC_ALLOW_DOCUMENTS` debe seguir en `false`.

## Pasos de activación (una vez superada la puerta)

1. Colocar la clave del proyecto en `services/api/.env` (gitignored), en
   `TRAMITATRON_ANTHROPIC_API_KEY`. El asistente nunca ve el valor.
2. Poner `ANTHROPIC_ALLOW_DOCUMENTS=true` en el entorno de la API.
3. (Opcional) fijar `ANTHROPIC_MODEL` si se quiere otro modelo; por defecto
   `claude-opus-4-8`.
4. Reiniciar la API. En el arranque, el log dirá
   `Gateway: Anthropic (...); documentos externos: ON`.

## Verificación tras activar

- `GET /api/version` debe mostrar `"ai_provider": "anthropic"` y
  `"documents_to_ai": true`. Este endpoint es la señal para soporte de qué
  postura de datos corre en cada despliegue.
- Escanear un DNI de PRUEBA (nunca uno real en la primera prueba) y comprobar
  que la extracción es coherente y que, con imagen ilegible, el kiosco pide
  repetir (confianza 0) en vez de inventar.
- Revisar los logs: NO debe aparecer ningún valor extraído (DNI, nombre, texto
  de carta). Solo tipos y estados.

## Vuelta atrás (rollback)

Poner `ANTHROPIC_ALLOW_DOCUMENTS=false` (o quitar la clave) y reiniciar. La
extracción vuelve a ser sintética al instante; no hay estado que migrar. La
voz nunca usa el proveedor, así que no se ve afectada.

## Qué NO activa la opción 3

- **Voz:** Claude no hace STT; la transcripción sigue siendo sintética (mock)
  hasta integrar un proveedor de voz aparte.
- **Conectores reales / portal real:** es otra puerta (worker + EIPD del
  portal, ADR-007). La opción 3 solo abre la lectura de documentos.

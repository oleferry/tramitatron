# ADR-007 — Worker de navegación asistida: preparar y ceder, nunca reservar

- **Estado:** aceptado
- **Fecha:** 2026-07-21
- **Contexto:** PRD §12.3, EPIC 5 (TT-502, TT-505), reglas 5, 7, 8 del §30

## Contexto

Fase 3: conectores reales con Playwright. La tentación es "automatizar el
trámite de punta a punta". El PRD lo prohíbe explícitamente: no se automatizan
CAPTCHAs, firma, Cl@ve ni credenciales (regla 5), la IA no navega URLs
arbitrarias (regla 7), y el worker de navegador es un servicio separado del
monolito (regla 8). Además, dirigir la automatización a un portal real de la
administración está sujeto a las pruebas de privacidad y a la EIPD (CLAUDE.md,
PRD §5.4).

## Decisión

Se crea `services/browser-worker`, un servicio FastAPI **separado** que:

### 1. Prepara y cede (nunca reserva)

`prepare` navega el portal, precompleta los campos **seguros** (matrícula, tipo
de vehículo…) y **se detiene** en el punto de handoff: CAPTCHA, identificación
(Cl@ve/certificado) y confirmación las hace la persona. El resultado terminal
del worker es siempre `user_handoff`; nunca `completed`, nunca envía el
formulario. Los campos de CAPTCHA/credenciales/firma están en una lista que el
worker jamás rellena, aunque lleguen en la petición.

### 2. Allowlist estricta (regla 7)

Cada conector declara sus hosts permitidos. El worker rechaza cualquier URL
cuyo host no esté en la allowlist. No hay navegación a URLs arbitrarias.

### 3. Dos drivers intercambiables (regla 11)

- **SimulatedDriver** (por defecto): httpx contra un **portal de pruebas local**
  renderizado en el servidor. Hace HTTP de verdad —navega, lee los campos reales
  del formulario, detecta el handoff— de forma reproducible y sin descargar
  navegadores. Es el driver de los tests y de la demo.
- **PlaywrightDriver** (extra opcional): Chromium real, con contexto de
  navegador nuevo por preparación (aislamiento, TT-502). Para portales con
  JavaScript. Verificado en local contra el portal de pruebas.

El portal de pruebas rechaza el POST con 403: si el worker intentara enviar el
formulario (lo que no hace), el fallo sería ruidoso.

### 4. Healthchecks sintéticos (TT-505)

`healthcheck` abre el portal y comprueba que el formulario esperado sigue
teniendo sus campos. No rellena ni reserva. Si faltan campos, marca el conector
no fiable (alerta por cambio del portal).

### 5. Portales reales, declarados pero DESACTIVADOS

GVA Salud y SITVAL se registran con su allowlist y su mapa de campos, pero
nacen `enabled=False`: `prepare` responde `unavailable`. Habilitarlos exige
completar privacidad/EIPD y, aun así, seguirán siendo preparar-y-ceder por el
CAPTCHA/Cl@ve. Esta ADR deja la estructura lista; no cruza esa puerta.

## Estado y prueba

- El worker, la allowlist, el handoff, el timeout, los eventos, el gateo de
  portales reales y los healthchecks están cubiertos por tests con el driver
  simulado (sin navegador).
- El **driver de Playwright se ejecutó en local** contra el portal de pruebas:
  navega, precompleta matrícula y tipo, y se detiene en el CAPTCHA con
  `user_handoff`. La prueba en vivo detectó y corrigió un fallo real (los
  `<select>` no admiten `fill`; requieren `select_option`).
- Falta por hacer (siguiente incremento): conectar el worker al API y al kiosco
  (pantalla de handoff que muestra a la persona la URL oficial y los pasos que
  le quedan), y, más adelante y solo tras la EIPD, habilitar un portal real.

## Alternativas descartadas

- **Automatizar el trámite completo, incluido el CAPTCHA.** Prohibido por la
  regla 5 y, con audio-CAPTCHA, es justo el fallo que hundió el prototipo legacy
  (PRD §4). Descartado.
- **Meter Playwright en el monolito de la API.** Rompe la regla 8 (worker
  separado) y acopla el ciclo de vida del navegador al de la API. Descartado.

"""Orquestación de la navegación asistida (TT-502).

`prepare` navega el portal, precompleta los campos seguros y SE DETIENE en el
punto de handoff (CAPTCHA, identificación, confirmación), devolviendo el estado
para que la persona termine. Nunca envía el formulario ni reserva.

`healthcheck` es sintético (TT-505): comprueba que el formulario esperado sigue
existiendo. No rellena ni reserva; solo mira.
"""

import asyncio
from collections.abc import Awaitable, Callable

from .drivers.base import BrowserDriver
from .models import HealthResult, PrepareResult, StepEvent
from .registry import PortalSpec

DriverFactory = Callable[[], Awaitable[BrowserDriver]]

# Tope de pasos del asistente: red de seguridad contra bucles (portales rotos o
# que se redirigen a sí mismos). Una cita previa real tiene 3-5 pasos.
_MAX_STEPS = 8

# Campos que jamás precompleta el worker aunque lleguen (regla 5): son de la
# persona. El field_map de cada portal ya excluye estos, pero se deja explícito.
_NEVER_FILL = {"captcha", "password", "clave", "pin", "otp", "firma", "cvv"}


def _at_handoff(text: str, signals: tuple[str, ...]) -> bool:
    """La página actual es el muro de la persona: hay CAPTCHA/identificación."""
    lowered = text.lower()
    return any(s in lowered for s in signals)


def _detect_pending(text: str, signals: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    pending: list[str] = []
    if "captcha" in lowered:
        pending.append("captcha")
    if any(s in lowered for s in ("cl@ve", "clave", "certificado")):
        pending.append("identificación")
    # Enviar/confirmar siempre lo hace la persona.
    pending.append("confirmar")
    # Dedup conservando orden.
    return list(dict.fromkeys(pending))


async def prepare(
    spec: PortalSpec,
    fields: dict[str, str],
    make_driver: DriverFactory,
    timeout_seconds: float,
) -> PrepareResult:
    if not spec.enabled:
        return PrepareResult(
            status="unavailable",
            connector=spec.connector,
            message=(
                "Este conector todavía no está habilitado. Dirigir la navegación a "
                "un portal real requiere completar las pruebas de privacidad y la "
                "EIPD (PRD §5.4)."
            ),
        )
    if not spec.allows(spec.start_url):
        return PrepareResult(
            status="error",
            connector=spec.connector,
            message="URL de inicio fuera de la allowlist.",
        )

    events: list[StepEvent] = []

    async def run() -> PrepareResult:
        driver = await make_driver()
        try:
            await driver.open(spec.start_url)
            events.append(StepEvent(kind="navigate", detail=spec.start_url))

            prefilled: list[str] = []
            text = ""
            # Recorre el asistente paso a paso: en cada página rellena lo que
            # puede y avanza, hasta llegar al muro de la persona (CAPTCHA/Cl@ve)
            # o quedarse sin 'Siguiente' que seguir.
            for _ in range(_MAX_STEPS):
                names = await driver.field_names()
                events.append(StepEvent(kind="read", detail=f"{len(names)} campos"))

                for logical, form_name in spec.field_map.items():
                    value = fields.get(logical)
                    if (
                        not value
                        or logical in prefilled
                        or form_name in _NEVER_FILL
                        or form_name not in names
                    ):
                        continue
                    await driver.fill(form_name, value)
                    prefilled.append(logical)
                    # El evento registra el nombre del campo, nunca el valor (PII).
                    events.append(StepEvent(kind="fill", detail=form_name))

                text = await driver.page_text()
                if _at_handoff(text, spec.handoff_signals):
                    break

                # El salto solo se permite dentro de la allowlist (regla 7): el
                # worker valida el destino ANTES de que el driver lo abra.
                target = await driver.next_target()
                if target is None or not spec.allows(target):
                    break
                await driver.advance()
                events.append(StepEvent(kind="advance", detail=target))

            pending = _detect_pending(text, spec.handoff_signals)
            url = await driver.current_url()
            events.append(StepEvent(kind="handoff", detail=", ".join(pending)))

            return PrepareResult(
                status="user_handoff",
                connector=spec.connector,
                url=url,
                prefilled=prefilled,
                pending=pending,
                events=events,
            )
        finally:
            await driver.close()

    try:
        return await asyncio.wait_for(run(), timeout=timeout_seconds)
    except TimeoutError:
        events.append(StepEvent(kind="error", detail="timeout"))
        return PrepareResult(
            status="error",
            connector=spec.connector,
            events=events,
            message="El portal ha tardado demasiado en responder.",
        )
    except Exception as exc:  # noqa: BLE001 - el worker no puede tumbar la API
        events.append(StepEvent(kind="error", detail=type(exc).__name__))
        return PrepareResult(
            status="error",
            connector=spec.connector,
            events=events,
            message="No se ha podido preparar el trámite en el portal.",
        )


async def healthcheck(
    spec: PortalSpec, make_driver: DriverFactory, timeout_seconds: float
) -> HealthResult:
    if not spec.enabled:
        return HealthResult(connector=spec.connector, healthy=False, detail="desactivado")

    async def run() -> HealthResult:
        driver = await make_driver()
        try:
            await driver.open(spec.start_url)
            expected = set(spec.field_map.values()) - _NEVER_FILL
            seen: set[str] = set()
            # Recorre el asistente reuniendo los campos de todas las páginas.
            for _ in range(_MAX_STEPS):
                seen |= await driver.field_names()
                if expected <= seen:
                    break
                target = await driver.next_target()
                if target is None or not spec.allows(target):
                    break
                await driver.advance()

            missing = expected - seen
            if missing:
                # TT-505: alerta por cambio. Si el asistente ya no tiene los
                # campos esperados, el portal ha cambiado y el conector no es fiable.
                return HealthResult(
                    connector=spec.connector,
                    healthy=False,
                    detail=f"faltan campos: {sorted(missing)}",
                )
            return HealthResult(
                connector=spec.connector, healthy=True, detail="formulario presente"
            )
        finally:
            await driver.close()

    try:
        return await asyncio.wait_for(run(), timeout=timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        return HealthResult(
            connector=spec.connector, healthy=False, detail=f"inaccesible ({type(exc).__name__})"
        )

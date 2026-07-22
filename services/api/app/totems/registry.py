"""Registro de tótems en memoria (TT-601).

Mantiene el parque DECLARADO (infra/totems.yaml) y superpone el estado EN VIVO
que llega por latido. Deriva el estado operativo de cada tótem:

- online   → latido reciente y periféricos sanos,
- degraded → latido reciente pero algún periférico caído o papel muy bajo,
- offline  → sin latido dentro de la ventana (o nunca reportó estando declarado),
- unknown  → declarado y sin ningún latido todavía.

Todo vive en memoria del proceso (se reinicia con la API), igual que las
métricas. El reloj es inyectable para tests deterministas.
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from .loader import DeclaredTotem
from .models import (
    FleetSummary,
    FleetView,
    Peripherals,
    TotemState,
    TotemStatus,
)

# Papel por debajo de este porcentaje: el tótem se marca «degraded».
_LOW_PAPER = 10


def _default_clock() -> datetime:
    return datetime.now(UTC)


@dataclass
class _Live:
    version: str
    peripherals: Peripherals
    last_seen: datetime


class TotemRegistry:
    def __init__(
        self,
        declared: list[DeclaredTotem] | None = None,
        now: Callable[[], datetime] | None = None,
        offline_after_seconds: float = 180.0,
        current_version: str | None = None,
    ) -> None:
        self._now = now or _default_clock
        self._offline_after = offline_after_seconds
        self._current_version = current_version
        self._declared = {t.id: t for t in (declared or [])}
        self._live: dict[str, _Live] = {}
        self._lock = threading.Lock()

    def heartbeat(self, totem_id: str, version: str, peripherals: Peripherals) -> None:
        with self._lock:
            self._live[totem_id] = _Live(
                version=version, peripherals=peripherals, last_seen=self._now()
            )

    def _derive(self, live: _Live | None, now: datetime) -> tuple[TotemState, float | None]:
        if live is None:
            return "unknown", None
        age = (now - live.last_seen).total_seconds()
        if age > self._offline_after:
            return "offline", age
        p = live.peripherals
        any_down = "down" in (p.camera, p.scanner, p.printer)
        if any_down or p.paper_level < _LOW_PAPER:
            return "degraded", age
        return "online", age

    def _status(self, totem_id: str, now: datetime) -> TotemStatus:
        declared = self._declared.get(totem_id)
        live = self._live.get(totem_id)
        state, age = self._derive(live, now)
        # Un tótem declarado que aún no ha reportado no es "unknown" indefinido:
        # el operador espera verlo, así que lo mostramos como offline.
        if live is None and declared is not None:
            state = "offline"
        version = live.version if live else None
        outdated = bool(
            version and self._current_version and version != self._current_version
        )
        return TotemStatus(
            id=totem_id,
            label=declared.label if declared else None,
            municipality=declared.municipality if declared else None,
            state=state,
            version=version,
            peripherals=live.peripherals if live else None,
            last_seen=live.last_seen.isoformat(timespec="seconds") if live else None,
            seconds_since_seen=round(age, 1) if age is not None else None,
            declared=declared is not None,
            auto_registered=declared is None,
            outdated=outdated,
        )

    def _ids(self) -> list[str]:
        # Declarados primero (en su orden); luego los de alta automática, ordenados.
        extra = sorted(tid for tid in self._live if tid not in self._declared)
        return list(self._declared.keys()) + extra

    def get(self, totem_id: str) -> TotemStatus | None:
        now = self._now()
        with self._lock:
            if totem_id not in self._declared and totem_id not in self._live:
                return None
            return self._status(totem_id, now)

    def snapshot(self) -> FleetView:
        now = self._now()
        with self._lock:
            statuses = [self._status(tid, now) for tid in self._ids()]
        counts = {"online": 0, "degraded": 0, "offline": 0, "unknown": 0}
        for s in statuses:
            counts[s.state] += 1
        return FleetView(
            generated_at=now.isoformat(timespec="seconds"),
            offline_after_seconds=self._offline_after,
            current_version=self._current_version,
            summary=FleetSummary(total=len(statuses), **counts),
            totems=statuses,
        )

"""Registro de incidencias en memoria (TT-603).

Guarda incidencias operativas para el panel de soporte: código anónimo,
componente, severidad, error técnico REDACTADO, tótem afectado y resolución.
Nada personal (PRD §13.4); el error se redacta al abrir.

Como el resto del panel, vive en memoria del proceso y se reinicia con la API.
Se conservan las últimas N incidencias (anillo) para no crecer sin límite. El
reloj es inyectable para tests; el código usa `secrets` (no el reloj), así que
es único aunque el reloj esté congelado en un test.
"""

import secrets
import threading
from collections import OrderedDict
from collections.abc import Callable
from datetime import UTC, datetime

from .models import (
    Component,
    Incident,
    IncidentReport,
    IncidentStatus,
    IncidentSummary,
    Severity,
)
from .redact import redact

_SEVERITIES = ("S1", "S2", "S3", "S4")


def _default_clock() -> datetime:
    return datetime.now(UTC)


class IncidentRegistry:
    def __init__(
        self,
        now: Callable[[], datetime] | None = None,
        max_incidents: int = 500,
    ) -> None:
        self._now = now or _default_clock
        self._max = max_incidents
        self._items: OrderedDict[str, Incident] = OrderedDict()
        self._lock = threading.Lock()

    def _new_code(self) -> str:
        # Código anónimo legible para el ciudadano (§5, «código de incidencia
        # anónimo»). No codifica nada: es aleatorio.
        return "INC-" + secrets.token_hex(3).upper()

    def open(
        self,
        component: Component,
        technical_error: str | None = None,
        severity: Severity = "S3",
        connector: str | None = None,
        totem_id: str | None = None,
    ) -> Incident:
        now = self._now().isoformat(timespec="seconds")
        with self._lock:
            code = self._new_code()
            while code in self._items:  # colisión improbable; garantía por si acaso
                code = self._new_code()
            incident = Incident(
                code=code,
                component=component,
                connector=connector,
                severity=severity,
                technical_error=redact(technical_error),
                totem_id=totem_id,
                status="open",
                created_at=now,
                updated_at=now,
                resolution=None,
            )
            self._items[code] = incident
            while len(self._items) > self._max:
                self._items.popitem(last=False)  # descarta la más antigua
            return incident

    def open_from_report(self, report: IncidentReport) -> Incident:
        return self.open(
            component=report.component,
            technical_error=report.technical_error,
            severity=report.severity,
            connector=report.connector,
            totem_id=report.totem_id,
        )

    def resolve(self, code: str, note: str = "") -> Incident | None:
        with self._lock:
            incident = self._items.get(code)
            if incident is None:
                return None
            updated = incident.model_copy(
                update={
                    "status": "resolved",
                    "resolution": redact(note) if note else "resuelta",
                    "updated_at": self._now().isoformat(timespec="seconds"),
                }
            )
            self._items[code] = updated
            return updated

    def get(self, code: str) -> Incident | None:
        with self._lock:
            return self._items.get(code)

    def list(
        self,
        status: IncidentStatus | None = None,
        severity: Severity | None = None,
        component: str | None = None,
    ) -> list[Incident]:
        with self._lock:
            items = list(self._items.values())
        if status is not None:
            items = [i for i in items if i.status == status]
        if severity is not None:
            items = [i for i in items if i.severity == severity]
        if component is not None:
            items = [i for i in items if i.component == component]
        # Más recientes primero.
        return list(reversed(items))

    def summary(self) -> IncidentSummary:
        with self._lock:
            items = list(self._items.values())
        by_sev = {s: 0 for s in _SEVERITIES}
        open_count = 0
        for i in items:
            by_sev[i.severity] += 1
            if i.status != "resolved":
                open_count += 1
        return IncidentSummary(total=len(items), open=open_count, by_severity=by_sev)

"""Registro de métricas agregadas (TT-602, PRD §18).

Observabilidad SIN vigilancia (PRD §18.2 y regla 11). Aquí solo viven
CONTADORES agregados: cuántas sesiones, en qué idioma, en qué franja horaria,
cuántos trámites se inician/completan/derivan/fallan/abandonan y una encuesta
de satisfacción 1–5. Nunca se guarda:

- identidad de sesión (ni el id aleatorio),
- texto, imágenes ni audio,
- nada que permita seguir a una persona entre sesiones o reidentificarla.

Todo está en memoria del proceso y se pierde al reiniciar: son métricas
operativas del piloto, no un registro histórico con valor legal. Si en el
futuro se persisten (PostgreSQL, PRD §9.2), lo que se guarda son estos mismos
agregados, jamás filas por persona.
"""

import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

# Eventos válidos por trámite. Se validan contra este conjunto para que nunca
# se pueda inyectar un contador arbitrario desde fuera.
PROCEDURE_EVENTS = ("started", "completed", "handoff", "failed", "abandoned")

# Canales asistidos que cuentan uso (no contenido).
CHANNELS = ("assistant", "letters", "voice", "documents")

_MIN_RATING, _MAX_RATING = 1, 5


@dataclass
class _ProcedureCounters:
    started: int = 0
    completed: int = 0
    handoff: int = 0
    failed: int = 0
    abandoned: int = 0


def _default_clock() -> datetime:
    return datetime.now(UTC)


class MetricsRegistry:
    """Contadores agregados thread-safe. El reloj es inyectable para tests."""

    def __init__(self, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or _default_clock
        self._lock = threading.Lock()
        self._started_at = self._now().isoformat(timespec="seconds")
        self._sessions_total = 0
        self._sessions_by_language: dict[str, int] = defaultdict(int)
        self._sessions_by_hour: dict[int, int] = defaultdict(int)
        self._procedures: dict[str, _ProcedureCounters] = defaultdict(_ProcedureCounters)
        self._channels: dict[str, int] = defaultdict(int)
        self._satisfaction: dict[int, int] = defaultdict(int)

    # --- Registro de eventos -------------------------------------------------

    def record_session(self, language: str) -> None:
        hour = self._now().hour
        with self._lock:
            self._sessions_total += 1
            self._sessions_by_language[language] += 1
            self._sessions_by_hour[hour] += 1

    def record_procedure(self, procedure_id: str, event: str) -> None:
        if event not in PROCEDURE_EVENTS:
            raise ValueError(f"Evento de trámite desconocido: {event!r}")
        with self._lock:
            counters = self._procedures[procedure_id]
            setattr(counters, event, getattr(counters, event) + 1)

    def record_channel(self, channel: str) -> None:
        if channel not in CHANNELS:
            raise ValueError(f"Canal desconocido: {channel!r}")
        with self._lock:
            self._channels[channel] += 1

    def record_satisfaction(self, rating: int) -> None:
        if not _MIN_RATING <= rating <= _MAX_RATING:
            raise ValueError("La satisfacción se puntúa de 1 a 5")
        with self._lock:
            self._satisfaction[rating] += 1

    # --- Lectura -------------------------------------------------------------

    def snapshot(self) -> dict:
        """Vista agregada para el cuadro de mando. Solo números, sin identidad."""
        with self._lock:
            procedures = {pid: vars(c).copy() for pid, c in self._procedures.items()}
            sessions_total = self._sessions_total
            by_language = dict(self._sessions_by_language)
            by_hour = {h: self._sessions_by_hour.get(h, 0) for h in range(24)}
            channels = {c: self._channels.get(c, 0) for c in CHANNELS}
            satisfaction = {
                r: self._satisfaction.get(r, 0) for r in range(_MIN_RATING, _MAX_RATING + 1)
            }
            started_at = self._started_at

        totals = {ev: sum(p[ev] for p in procedures.values()) for ev in PROCEDURE_EVENTS}
        started = totals["started"]
        resolved = totals["completed"] + totals["handoff"]

        def _pct(part: int, whole: int) -> float | None:
            return round(100 * part / whole, 1) if whole else None

        sat_votes = sum(satisfaction.values())
        sat_avg = (
            round(sum(r * n for r, n in satisfaction.items()) / sat_votes, 2)
            if sat_votes
            else None
        )

        return {
            "generated_at": self._now().isoformat(timespec="seconds"),
            "since": started_at,
            "usage": {
                "sessions": sessions_total,
                "by_language": by_language,
                "by_hour": by_hour,
                "channels": channels,
            },
            "procedures": {
                "totals": totals,
                # Tasa de éxito: completados sobre iniciados (PRD §18.1 Eficiencia).
                "success_rate_pct": _pct(totals["completed"], started),
                # Derivaciones (handoff) sobre iniciados.
                "handoff_rate_pct": _pct(totals["handoff"], started),
                # Abandono: iniciados que no se resolvieron (ni completados ni derivados).
                "abandonment_rate_pct": _pct(max(started - resolved, 0), started),
                "by_procedure": procedures,
            },
            "satisfaction": {
                "votes": sat_votes,
                "average": sat_avg,
                "histogram": satisfaction,
            },
        }

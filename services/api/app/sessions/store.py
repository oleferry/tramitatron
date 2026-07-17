"""Contrato del almacén de sesiones efímeras.

Una sesión es anónima: identificador aleatorio, TTL, y datos A1/A2 que viven
solo en memoria/Redis y se purgan al cerrar o expirar. Nunca se persisten en
disco ni aparecen en logs.
"""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class Session:
    id: str
    language: str
    created_at: float
    expires_at: float
    data: dict[str, str] = field(default_factory=dict)


class SessionStore(Protocol):
    def create(self, language: str) -> Session: ...

    def get(self, session_id: str) -> Session | None:
        """Devuelve la sesión si existe y no ha expirado; una expirada se purga."""
        ...

    def extend(self, session_id: str) -> Session | None:
        """Renueva el TTL (prolongación explícita con trámite abierto)."""
        ...

    def set_data(self, session_id: str, key: str, value: str) -> bool: ...

    def remove_data(self, session_id: str, key: str) -> bool:
        """Elimina una clave de datos concreta (p. ej. una extracción documental)."""
        ...

    def purge(self, session_id: str) -> bool:
        """Elimina la sesión y todos sus datos. Idempotente."""
        ...

    def active_count(self) -> int: ...

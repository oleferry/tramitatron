"""Almacén de sesiones en memoria (desarrollo y tests). En despliegue se usa Redis."""

import threading
import time
import uuid

from .store import Session


class MemorySessionStore:
    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def _now(self) -> float:
        return time.monotonic()

    def create(self, language: str) -> Session:
        now = self._now()
        session = Session(
            id=uuid.uuid4().hex,
            language=language,
            created_at=now,
            expires_at=now + self._ttl,
        )
        with self._lock:
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.expires_at <= self._now():
                self._wipe(session)
                return None
            return session

    def extend(self, session_id: str) -> Session | None:
        session = self.get(session_id)
        if session is None:
            return None
        with self._lock:
            session.expires_at = self._now() + self._ttl
        return session

    def set_data(self, session_id: str, key: str, value: str) -> bool:
        session = self.get(session_id)
        if session is None:
            return False
        with self._lock:
            session.data[key] = value
        return True

    def purge(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            self._wipe(session)
            return True

    def _wipe(self, session: Session) -> None:
        # Sobrescribe los datos antes de soltar la referencia; borrado demostrable.
        session.data.clear()
        self._sessions.pop(session.id, None)

    def active_count(self) -> int:
        now = self._now()
        with self._lock:
            expired = [s for s in self._sessions.values() if s.expires_at <= now]
            for session in expired:
                self._wipe(session)
            return len(self._sessions)

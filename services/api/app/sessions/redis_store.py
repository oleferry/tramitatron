"""Almacén de sesiones en Redis con TTL nativo (EXPIRE). Los datos viven solo
en la clave de la sesión; al expirar o purgar, Redis los elimina por completo."""

import json
import time
import uuid

import redis

from .store import Session

_PREFIX = "tramitatron:session:"


class RedisSessionStore:
    def __init__(self, url: str, ttl_seconds: float) -> None:
        self._ttl = max(1, int(ttl_seconds))
        self._client = redis.Redis.from_url(url, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return _PREFIX + session_id

    def create(self, language: str) -> Session:
        now = time.monotonic()
        session = Session(
            id=uuid.uuid4().hex,
            language=language,
            created_at=now,
            expires_at=now + self._ttl,
        )
        payload = json.dumps({"language": session.language, "data": {}})
        self._client.set(self._key(session.id), payload, ex=self._ttl)
        return session

    def get(self, session_id: str) -> Session | None:
        key = self._key(session_id)
        raw = self._client.get(key)
        if raw is None:
            return None
        ttl = self._client.ttl(key)
        stored = json.loads(raw)
        now = time.monotonic()
        return Session(
            id=session_id,
            language=stored["language"],
            created_at=now,  # no se conserva el instante real; no es necesario
            expires_at=now + max(ttl, 0),
            data=stored["data"],
        )

    def extend(self, session_id: str) -> Session | None:
        if not self._client.expire(self._key(session_id), self._ttl):
            return None
        return self.get(session_id)

    def set_data(self, session_id: str, key: str, value: str) -> bool:
        redis_key = self._key(session_id)
        raw = self._client.get(redis_key)
        if raw is None:
            return False
        stored = json.loads(raw)
        stored["data"][key] = value
        ttl = self._client.ttl(redis_key)
        self._client.set(redis_key, json.dumps(stored), ex=max(ttl, 1))
        return True

    def remove_data(self, session_id: str, key: str) -> bool:
        redis_key = self._key(session_id)
        raw = self._client.get(redis_key)
        if raw is None:
            return False
        stored = json.loads(raw)
        stored["data"].pop(key, None)
        ttl = self._client.ttl(redis_key)
        self._client.set(redis_key, json.dumps(stored), ex=max(ttl, 1))
        return True

    def purge(self, session_id: str) -> bool:
        return bool(self._client.delete(self._key(session_id)))

    def active_count(self) -> int:
        return sum(1 for _ in self._client.scan_iter(match=_PREFIX + "*"))

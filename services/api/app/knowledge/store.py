"""Almacén y recuperador del conocimiento oficial.

Carga la allowlist (sources.yaml), el índice de snapshots y sus textos, los
trocea en fragmentos y permite recuperar el más relevante para una consulta
mediante puntuación léxica determinista (sin IA): término normalizado a
término normalizado, ponderando los términos raros.

Si no hay snapshots, el sistema arranca igualmente y responde "no encontrado"
(degradación segura, PRD §6.13).
"""

import json
import math
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import yaml

from .models import KnowledgeSource, SnapshotMeta

_CHUNK_MAX_CHARS = 700
_EXCERPT_MAX_CHARS = 600

# Mini-lista de vacías es/va: suficiente para puntuación léxica.
_STOPWORDS = {
    "a", "al", "amb", "como", "con", "de", "del", "el", "els", "en", "es",
    "este", "esta", "hay", "i", "la", "las", "les", "lo", "los", "meu", "mi",
    "necesito", "necessite", "no", "o", "para", "pedir", "per", "porque",
    "puc", "puedo", "que", "què", "qué", "se", "si", "sin", "sobre", "su",
    "teu", "tu", "un", "una", "vull", "y", "yo", "quiero", "cómo", "com",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{3,}", _normalize(text)) if t not in _STOPWORDS]


@dataclass(frozen=True)
class Chunk:
    source_id: str
    text: str
    token_set: frozenset[str]
    prose_weight: float  # 0.25–1.0: penaliza fragmentos que son puro menú


def _prose_weight(text: str) -> float:
    """Un fragmento de navegación tiene muchas líneas de 1–3 palabras; la prosa
    real tiene frases. Pondera la media de palabras por línea."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.25
    avg_words = sum(len(line.split()) for line in lines) / len(lines)
    return max(0.25, min(1.0, avg_words / 8))


def _make_chunk(source_id: str, text: str) -> Chunk:
    return Chunk(source_id, text, frozenset(_tokens(text)), _prose_weight(text))


def _chunk_text(source_id: str, text: str) -> list[Chunk]:
    chunks: list[Chunk] = []
    buffer = ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if buffer and len(buffer) + len(paragraph) > _CHUNK_MAX_CHARS:
            chunks.append(_make_chunk(source_id, buffer))
            buffer = paragraph
        else:
            buffer = f"{buffer}\n\n{paragraph}" if buffer else paragraph
    if buffer:
        chunks.append(_make_chunk(source_id, buffer))
    return chunks


class KnowledgeStore:
    def __init__(self, knowledge_path: Path) -> None:
        self.sources: dict[str, KnowledgeSource] = {}
        self.snapshots: dict[str, SnapshotMeta] = {}
        self._chunks: list[Chunk] = []
        self._doc_freq: dict[str, int] = {}

        sources_file = knowledge_path / "sources.yaml"
        if sources_file.exists():
            raw = yaml.safe_load(sources_file.read_text(encoding="utf-8")) or {}
            for entry in raw.get("sources", []):
                source = KnowledgeSource.model_validate(entry)
                self.sources[source.id] = source

        index_file = knowledge_path / "snapshots" / "index.json"
        if index_file.exists():
            for entry in json.loads(index_file.read_text(encoding="utf-8")):
                meta = SnapshotMeta.model_validate(entry)
                self.snapshots[meta.source_id] = meta
                if meta.status == "ok" and meta.text_file:
                    text_path = knowledge_path / "snapshots" / meta.text_file
                    if text_path.exists() and meta.source_id in self.sources:
                        self._chunks.extend(
                            _chunk_text(meta.source_id, text_path.read_text(encoding="utf-8"))
                        )

        for chunk in self._chunks:
            for token in chunk.token_set:
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1

    def retrieve(self, query: str, procedure_id: str | None = None) -> Chunk | None:
        """Mejor fragmento para la consulta, o None si nada es suficientemente
        relevante. Con procedure_id, las fuentes de ese trámite tienen prioridad
        estricta: una pregunta hecha dentro de un trámite debe responderse con
        SU organismo, y solo si sus fuentes no dicen nada se busca en el resto."""
        query_tokens = set(_tokens(query))
        if not query_tokens or not self._chunks:
            return None

        preferred_sources = {
            s.id for s in self.sources.values() if procedure_id in s.procedure_ids
        }

        def score(chunk: Chunk) -> float:
            matched = query_tokens & chunk.token_set
            if not matched:
                return 0.0
            total = len(self._chunks)
            value = sum(
                1.0 + math.log(total / (1 + self._doc_freq.get(t, 0))) for t in matched
            )
            return value * chunk.prose_weight

        def best_of(chunks: list[Chunk], min_matched: int) -> Chunk | None:
            if not chunks:
                return None
            best = max(chunks, key=score)
            matched = query_tokens & best.token_set
            if len(matched) < min(min_matched, len(query_tokens)):
                return None
            return best

        # En las fuentes del trámite basta 1 término: el contexto ya acota
        # ("renovar" no casa con "renovación" al no haber stemming, y exigir
        # 2 términos expulsaba la consulta hacia fuentes de otros organismos).
        if preferred_sources:
            preferred = best_of(
                [c for c in self._chunks if c.source_id in preferred_sources],
                min_matched=1,
            )
            if preferred is not None:
                return preferred
        # Fuera del trámite, el umbral de 2 términos evita respuestas por ruido.
        return best_of(self._chunks, min_matched=2)

    def excerpt(self, chunk: Chunk, query: str = "") -> str:
        text = chunk.text.strip()
        # Empieza en la primera línea que contiene un término de la consulta,
        # para no abrir el extracto con cabeceras o navegación irrelevante.
        query_tokens = set(_tokens(query))
        if query_tokens and len(text) > _EXCERPT_MAX_CHARS:
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if query_tokens & set(_tokens(line)):
                    text = "\n".join(lines[i:]).strip()
                    break
        if len(text) <= _EXCERPT_MAX_CHARS:
            return text
        cut = text[:_EXCERPT_MAX_CHARS]
        # Corta en el último final de frase para no dejar texto a medias.
        last_stop = max(cut.rfind(". "), cut.rfind(".\n"))
        return cut[: last_stop + 1] if last_stop > 200 else cut + "…"

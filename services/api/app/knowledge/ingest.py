"""Ingesta de fuentes oficiales (PRD §16.2).

    python -m app.knowledge.ingest [--knowledge-path RUTA]

Para cada fuente de la allowlist: descarga la página, extrae el texto, calcula
el hash y —solo si el contenido cambió— escribe un snapshot nuevo. El index.json
apunta siempre al snapshot vigente; el historial queda en git (versionado).
Una fuente que falla se marca "error" y el asistente deja de usarla
(despublicación automática, PRD §16.2).
"""

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

import yaml

from .models import KnowledgeSource, SnapshotMeta

_USER_AGENT = "Tramitatron-Ingest/0.1 (punto de asistencia digital; contacto en el repositorio)"
_TIMEOUT_SECONDS = 30
_SKIP_TAGS = {"script", "style", "noscript", "svg", "iframe", "head"}


class _TextExtractor(HTMLParser):
    """Extractor de texto plano con separación por bloques."""

    _BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "br", "tr", "section", "article"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "meta":
            # En webs SPA el cuerpo llega vacío; el título y la descripción
            # oficiales de las metaetiquetas son el único texto disponible.
            attr_map = dict(attrs)
            if attr_map.get("name") == "description" or attr_map.get("property") in (
                "og:title",
                "og:description",
            ):
                content = (attr_map.get("content") or "").strip()
                if content:
                    self._parts.append(f"\n{content}\n")
        if tag in _SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        elif tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)

    @staticmethod
    def _is_content_line(line: str) -> bool:
        # Filtra la morralla de navegación: se conservan las líneas con al
        # menos 3 palabras o que terminan como una frase.
        return len(line.split()) >= 3 or line.endswith((".", ":", "?", "!"))

    def text(self) -> str:
        raw = "".join(self._parts)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in raw.splitlines()]
        collapsed = "\n".join(line for line in lines if line and self._is_content_line(line))
        return re.sub(r"\n{2,}", "\n\n", collapsed)


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
        html = response.read().decode(response.headers.get_content_charset() or "utf-8", "replace")
    extractor = _TextExtractor()
    extractor.feed(html)
    return extractor.text()


def ingest(knowledge_path: Path) -> int:
    raw = yaml.safe_load((knowledge_path / "sources.yaml").read_text(encoding="utf-8"))
    sources = [KnowledgeSource.model_validate(e) for e in raw.get("sources", [])]

    snapshots_dir = knowledge_path / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    index_file = snapshots_dir / "index.json"
    previous: dict[str, SnapshotMeta] = {}
    if index_file.exists():
        for entry in json.loads(index_file.read_text(encoding="utf-8")):
            meta = SnapshotMeta.model_validate(entry)
            previous[meta.source_id] = meta

    now = datetime.now(UTC).isoformat(timespec="seconds")
    results: list[SnapshotMeta] = []
    failures = 0

    for source in sources:
        try:
            text = fetch_text(str(source.url))
            if len(text) < 200:
                raise ValueError(f"contenido demasiado corto ({len(text)} caracteres)")
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            old = previous.get(source.id)
            if old and old.status == "ok" and old.sha256 == digest:
                print(f"  = {source.id}: sin cambios ({digest[:8]})")
                results.append(old)
                continue
            filename = f"{source.id}-{digest[:8]}.txt"
            (snapshots_dir / filename).write_text(text, encoding="utf-8")
            results.append(
                SnapshotMeta(
                    source_id=source.id,
                    fetched_at=now,
                    sha256=digest,
                    status="ok",
                    text_file=filename,
                )
            )
            marker = "~ CAMBIO DETECTADO" if old else "+"
            print(f"  {marker} {source.id}: {len(text)} caracteres ({digest[:8]})")
        except Exception as exc:  # noqa: BLE001 - una fuente caída no detiene la ingesta
            failures += 1
            print(f"  ! {source.id}: ERROR {exc}")
            results.append(
                SnapshotMeta(
                    source_id=source.id,
                    fetched_at=now,
                    sha256="",
                    status="error",
                    error=str(exc)[:200],
                )
            )

    index_file.write_text(
        json.dumps([m.model_dump() for m in results], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Ingesta terminada: {len(results) - failures} ok, {failures} con error.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingesta de fuentes oficiales")
    # services/api/app/knowledge/ingest.py -> cuatro niveles hasta la raíz del repo
    default_path = Path(__file__).resolve().parents[4] / "knowledge"
    parser.add_argument("--knowledge-path", type=Path, default=default_path)
    args = parser.parse_args()
    sys.exit(ingest(args.knowledge_path))

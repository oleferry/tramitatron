"""Carga y validación del catálogo declarativo desde YAML."""

from pathlib import Path

import yaml

from .models import Procedure


class CatalogError(Exception):
    pass


def load_catalog(path: Path) -> dict[str, Procedure]:
    if not path.is_dir():
        raise CatalogError(f"No existe el directorio de catálogo: {path}")

    procedures: dict[str, Procedure] = {}
    for yaml_file in sorted(path.glob("*.yaml")):
        raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        try:
            procedure = Procedure.model_validate(raw)
        except Exception as exc:
            raise CatalogError(f"Trámite inválido en {yaml_file.name}: {exc}") from exc
        if procedure.id in procedures:
            raise CatalogError(f"Id duplicado en el catálogo: {procedure.id}")
        procedures[procedure.id] = procedure

    if not procedures:
        raise CatalogError(f"El catálogo está vacío: {path}")
    return procedures

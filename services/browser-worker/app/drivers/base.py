"""Contrato del driver de navegación.

Dos implementaciones intercambiables (regla 11: sin acoplarse a un motor):
- SimulatedDriver: httpx contra el portal de pruebas local, sin navegador.
- PlaywrightDriver: Chromium real (extra opcional).

El driver solo sabe navegar, leer campos, rellenar y detectar el punto de
handoff. No sabe de trámites ni decide nada: eso vive en el worker.
"""

from typing import Protocol


class BrowserDriver(Protocol):
    async def open(self, url: str) -> None:
        """Navega a la URL (ya validada contra la allowlist por el worker)."""
        ...

    async def field_names(self) -> set[str]:
        """Nombres de los campos de formulario visibles en la página."""
        ...

    async def fill(self, name: str, value: str) -> None:
        """Escribe un valor en un campo. No envía el formulario."""
        ...

    async def page_text(self) -> str:
        """Texto/HTML de la página, para detectar señales de handoff."""
        ...

    async def current_url(self) -> str: ...

    async def close(self) -> None: ...

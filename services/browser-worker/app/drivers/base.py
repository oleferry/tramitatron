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

    async def next_target(self) -> str | None:
        """URL a la que avanzaría el formulario actual por GET (el 'Siguiente'
        del asistente), ya resuelta como absoluta. Devuelve None si el
        formulario es POST (envío final) o no hay formulario: ahí no se avanza.
        El worker valida esa URL contra la allowlist ANTES de pedir avanzar."""
        ...

    async def advance(self) -> None:
        """Avanza al siguiente paso del asistente (GET del 'Siguiente'). Nunca
        envía el formulario final (POST): eso es la confirmación de la persona."""
        ...

    async def close(self) -> None: ...

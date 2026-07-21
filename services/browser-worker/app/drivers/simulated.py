"""Driver simulado: httpx contra el portal de pruebas local, sin navegador.

Hace HTTP de verdad (GET del formulario, lectura de los campos reales del HTML),
así que ejercita el flujo completo de principio a fin de forma reproducible y
sin descargar Chromium. Es el driver por defecto y el de los tests.

No sirve para portales SPA con mucho JavaScript —para eso está el driver de
Playwright—, pero el portal de pruebas es HTML renderizado en el servidor, que
es justo lo que este driver sabe leer.
"""

from html.parser import HTMLParser

import httpx


class _FormFields(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.names: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"input", "select", "textarea"}:
            attr = dict(attrs)
            if attr.get("name"):
                self.names.add(attr["name"])


class SimulatedDriver:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._html = ""
        self._url = ""
        self._values: dict[str, str] = {}

    async def open(self, url: str) -> None:
        response = await self._client.get(url)
        response.raise_for_status()
        self._html = response.text
        self._url = url
        self._values = {}

    async def field_names(self) -> set[str]:
        parser = _FormFields()
        parser.feed(self._html)
        return parser.names

    async def fill(self, name: str, value: str) -> None:
        # "Rellenar" = registrar el valor. Nunca se envía el formulario: no hay
        # POST en ningún punto de este driver.
        self._values[name] = value

    async def page_text(self) -> str:
        return self._html

    async def current_url(self) -> str:
        return self._url

    async def close(self) -> None:
        # El cliente httpx lo gestiona quien lo crea (la app), no el driver.
        return None

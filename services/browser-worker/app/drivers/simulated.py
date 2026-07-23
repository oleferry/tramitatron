"""Driver simulado: httpx contra el portal de pruebas local, sin navegador.

Hace HTTP de verdad (GET del formulario, lectura de los campos reales del HTML)
y navega el asistente de varias páginas siguiendo el 'Siguiente' de cada paso
por GET. Así ejercita el flujo completo de principio a fin de forma
reproducible y sin descargar Chromium. Es el driver por defecto y el de los
tests.

Regla clave: solo avanza formularios GET (los pasos del asistente). El envío
final es POST y el worker nunca lo pide: esa es la confirmación de la persona.

No sirve para portales SPA con mucho JavaScript —para eso está el driver de
Playwright—, pero el portal de pruebas es HTML renderizado en el servidor, que
es justo lo que este driver sabe leer.
"""

from html.parser import HTMLParser
from urllib.parse import urljoin

import httpx


class _FormParser(HTMLParser):
    """Lee los campos y el primer formulario (su action y method)."""

    def __init__(self) -> None:
        super().__init__()
        self.names: set[str] = set()
        self.form_action: str | None = None
        self.form_method: str = "get"
        self._seen_form = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = dict(attrs)
        if tag == "form" and not self._seen_form:
            self._seen_form = True
            self.form_action = attr.get("action")
            self.form_method = (attr.get("method") or "get").lower()
        if tag in {"input", "select", "textarea"} and attr.get("name"):
            self.names.add(attr["name"])


class SimulatedDriver:
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._html = ""
        self._url = ""
        self._values: dict[str, str] = {}
        self._names: set[str] = set()
        self._action: str | None = None
        self._method = "get"

    def _parse(self, html: str) -> None:
        parser = _FormParser()
        parser.feed(html)
        self._names = parser.names
        self._action = parser.form_action
        self._method = parser.form_method

    async def open(self, url: str) -> None:
        response = await self._client.get(url)
        response.raise_for_status()
        self._url = url
        self._html = response.text
        self._values = {}
        self._parse(self._html)

    async def field_names(self) -> set[str]:
        return set(self._names)

    async def fill(self, name: str, value: str) -> None:
        # "Rellenar" = registrar el valor. Se arrastra como parámetros al avanzar
        # de paso (GET), igual que haría un formulario del asistente. Nunca se
        # hace POST: no hay envío final en ningún punto de este driver.
        self._values[name] = value

    async def page_text(self) -> str:
        return self._html

    async def current_url(self) -> str:
        return self._url

    async def next_target(self) -> str | None:
        if not self._action or self._method != "get":
            return None
        return urljoin(self._url, self._action)

    async def advance(self) -> None:
        target = await self.next_target()
        if target is None:
            return
        # Los valores acumulados viajan como parámetros del 'Siguiente'.
        response = await self._client.get(target, params=self._values)
        response.raise_for_status()
        self._url = str(response.url)
        self._html = response.text
        self._parse(self._html)

    async def submit_target(self) -> str | None:
        if not self._action or self._method != "post":
            return None
        return urljoin(self._url, self._action)

    async def submit(self) -> str:
        # Envío final (POST). Solo se llega aquí con confirmación explícita del
        # ciudadano en un trámite completable; el worker lo valida antes.
        target = await self.submit_target()
        if target is None:
            raise RuntimeError("no hay formulario de envío en la página actual")
        response = await self._client.post(target, data=self._values)
        response.raise_for_status()
        self._url = str(response.url)
        self._html = response.text
        self._parse(self._html)
        return self._html

    async def close(self) -> None:
        # El cliente httpx lo gestiona quien lo crea (la app), no el driver.
        return None

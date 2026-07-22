"""Driver real con Playwright (Chromium). Extra opcional.

Mismo contrato que el simulado, pero con un navegador de verdad, capaz de
manejar portales con JavaScript. Se usa solo si se instala el extra
(`pip install -e ".[playwright]"` y `playwright install chromium`) y se
selecciona con BROWSER_DRIVER=playwright.

Aislamiento (TT-502): cada preparación usa un contexto de navegador nuevo, sin
cookies ni almacenamiento previos, y se cierra al terminar. Nada persiste entre
personas.
"""

from typing import Any


class PlaywrightDriver:
    """Envuelve una página de Playwright ya abierta en un contexto aislado.

    Se construye con la fábrica `launch()` para que el import de playwright sea
    perezoso: el worker no depende del paquete salvo cuando este driver se usa.
    """

    def __init__(self, playwright: Any, browser: Any, context: Any, page: Any) -> None:
        self._pw = playwright
        self._browser = browser
        self._context = context
        self._page = page

    @classmethod
    async def launch(cls) -> "PlaywrightDriver":
        from playwright.async_api import async_playwright

        pw = await async_playwright().start()
        browser = await pw.chromium.launch(headless=True)
        # Contexto nuevo = sesión limpia, sin datos de nadie (aislamiento).
        context = await browser.new_context()
        page = await context.new_page()
        return cls(pw, browser, context, page)

    async def open(self, url: str) -> None:
        await self._page.goto(url, wait_until="domcontentloaded")

    async def field_names(self) -> set[str]:
        names = await self._page.eval_on_selector_all(
            "input[name], select[name], textarea[name]",
            "els => els.map(e => e.getAttribute('name'))",
        )
        return {n for n in names if n}

    async def fill(self, name: str, value: str) -> None:
        # Rellena el campo por nombre. No pulsa ningún botón de envío.
        # Los <select> no admiten fill: hay que elegir la opción.
        selector = f"[name=\"{name}\"]"
        tag = await self._page.eval_on_selector(selector, "el => el.tagName.toLowerCase()")
        if tag == "select":
            await self._page.select_option(selector, value)
        else:
            await self._page.fill(selector, value)

    async def page_text(self) -> str:
        return await self._page.content()

    async def current_url(self) -> str:
        return self._page.url

    async def next_target(self) -> str | None:
        # Lee el primer formulario. `el.action` en el DOM ya es una URL absoluta.
        forms = await self._page.eval_on_selector_all(
            "form",
            "els => els.slice(0,1).map(f => "
            "({action: f.action, method: (f.method||'get').toLowerCase()}))",
        )
        if not forms:
            return None
        info = forms[0]
        if info.get("method") != "get":
            return None
        return info.get("action") or None

    async def advance(self) -> None:
        # Pulsa el 'Siguiente' del paso (un submit de un formulario GET) y espera
        # la navegación. El worker solo llama aquí cuando next_target no es None,
        # es decir, cuando el formulario es GET: nunca se envía el POST final.
        await self._page.click(
            "button[type=submit], input[type=submit], form button:not([type])"
        )
        await self._page.wait_for_load_state("domcontentloaded")

    async def close(self) -> None:
        await self._context.close()
        await self._browser.close()
        await self._pw.stop()

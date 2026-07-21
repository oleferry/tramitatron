# Worker de navegación asistida. Por defecto usa el driver simulado (httpx)
# contra el portal de pruebas local: reproducible y sin navegador.
#
# Para el driver real de Playwright, parte de la imagen oficial de Playwright
# (trae Chromium y las dependencias del sistema) y arranca con
# BROWSER_DRIVER=playwright y PORTAL_HOST apuntando al portal servido.
FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

EXPOSE 8220
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8220"]

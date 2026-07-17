# Imagen completa de la API para despliegue (contexto: raíz del repo).
# Incluye el catálogo declarativo y los snapshots de conocimiento oficial,
# que en desarrollo se montan como volúmenes.
FROM python:3.12-slim

WORKDIR /srv

COPY services/api/pyproject.toml ./
COPY services/api/app ./app
RUN pip install --no-cache-dir .

COPY connectors/catalog ./connectors/catalog
COPY knowledge ./knowledge

ENV CATALOG_PATH=/srv/connectors/catalog \
    KNOWLEDGE_PATH=/srv/knowledge

EXPOSE 8000
# Render (y otros PaaS) inyectan PORT; en local se usa 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

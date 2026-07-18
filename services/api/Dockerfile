FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# El catálogo y el conocimiento se montan como volúmenes de solo lectura
# en /catalog y /knowledge (ver compose). Sin KNOWLEDGE_PATH el RAG arranca
# vacío y el asistente responde siempre "no encontrado".
ENV CATALOG_PATH=/catalog
ENV KNOWLEDGE_PATH=/knowledge

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

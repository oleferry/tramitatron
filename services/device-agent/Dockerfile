# Simulador de periféricos para desarrollo. En el tótem real el agente se
# ejecuta como servicio local y escucha SOLO en localhost (PRD §17.2).
FROM python:3.12-slim

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

EXPOSE 8210
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8210"]

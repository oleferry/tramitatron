# Atajos de desarrollo. En Windows sin make, usa los comandos equivalentes del README.

.PHONY: install api agent kiosk test lint up

install:
	cd services/api && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
	cd services/device-agent && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]"
	cd apps/kiosk && npm install

api:
	cd services/api && .venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

agent:
	cd services/device-agent && .venv/Scripts/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8210

kiosk:
	cd apps/kiosk && npm run dev

test:
	cd services/api && .venv/Scripts/python -m pytest -q
	cd services/device-agent && .venv/Scripts/python -m pytest -q

lint:
	cd services/api && .venv/Scripts/python -m ruff check app tests
	cd services/device-agent && .venv/Scripts/python -m ruff check app tests
	cd apps/kiosk && npm run typecheck

up:
	docker compose up --build

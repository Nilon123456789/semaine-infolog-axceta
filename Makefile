.PHONY: up down build logs test cloud-test dashboard-build

up:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

cloud-test:
	cd services/cloud && pip install -r requirements-dev.txt && pytest -q && ruff check app tests

dashboard-build:
	cd services/dashboard && npm ci && npm run build && node scripts/format.test.mjs

test: cloud-test dashboard-build

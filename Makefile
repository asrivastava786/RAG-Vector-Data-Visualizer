.PHONY: dev test lint format migrate seed docker-up docker-down backend-test frontend-test

dev:
	docker compose up --build

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

test: backend-test frontend-test

backend-test:
	cd backend && pytest

frontend-test:
	cd frontend && npm run typecheck

lint:
	cd backend && ruff check app
	cd frontend && npm run lint

format:
	cd backend && ruff format app

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python scripts/seed.py


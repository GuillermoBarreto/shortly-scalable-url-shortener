.PHONY: install dev test lint check migrate
install:
	python -m pip install -e ".[dev]"
	cd frontend && npm ci
dev:
	uvicorn app.main:app --reload
test:
	pytest
	cd frontend && npm test
lint:
	ruff check .
	cd frontend && npm run lint
check: lint test
	cd frontend && npm run typecheck && npm run build
migrate:
	alembic upgrade head

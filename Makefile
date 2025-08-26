.PHONY: run dev test format lint build docker

run:
	uvicorn app.main:app --reload --port 8000

dev:
	UVICORN_RELOAD=true uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest -q

format:
	ruff check --fix . || true
	black .

lint:
	ruff check .

build:
	python -m build

docker:
	docker build -t ai-qa-assistant:latest .
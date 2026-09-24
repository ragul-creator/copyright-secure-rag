.PHONY: install install-prod test bootstrap api ui up down bom

install:
	python -m pip install -r requirements.txt

install-prod:
	python -m pip install -r requirements-production.txt

test:
	python -m pytest -q

bootstrap:
	PYTHONPATH=. python scripts/bootstrap_demo.py

api:
	PYTHONPATH=. uvicorn apps.api.main:app --reload

ui:
	PYTHONPATH=. streamlit run apps/ui/app.py

up:
	docker compose up --build

down:
	docker compose down

bom:
	PYTHONPATH=. python scripts/generate_cyclonedx_data_bom.py

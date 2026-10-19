VENV_DIR := .venv/bin
PYTHON := $(VENV_DIR)/python
PIP := $(VENV_DIR)/pip
PYTEST := $(VENV_DIR)/pytest
CELERY := $(VENV_DIR)/celery
DJANGO := $(PYTHON) manage.py

.PHONY: backup install migrate makemigrations shell_plus shell superuser run test lint format check worker beat up down

install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements/development.txt
	$(VENV_DIR)/pre-commit install || true

migrate:
	$(DJANGO) migrate

makemigrations:
	$(DJANGO) makemigrations

shell_plus:
	$(DJANGO) shell_plus

shell: shell_plus

superuser:
	$(DJANGO) createsuperuser

run:
	$(DJANGO) runserver

test:
	$(PYTEST)

lint:
	$(VENV_DIR)/ruff check .
	$(VENV_DIR)/black --check .
	$(VENV_DIR)/mypy .
	$(VENV_DIR)/bandit -r apps config -x '**/tests/**'

format:
	$(VENV_DIR)/ruff check --fix .
	$(VENV_DIR)/black .

# Usage: make backup [ARGS=--sync]  (queues on Celery if configured, else runs inline)
backup:
	$(DJANGO) backup_db $(ARGS)

check:
	$(DJANGO) check

worker:
	$(CELERY) -A config worker -l info

beat:
	$(CELERY) -A config beat -l info

up:
	docker compose up --build

down:
	docker compose down

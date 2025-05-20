SHELL := /bin/bash

.PHONY: help install test test-unit test-integration lint run build clean docker-build docker-run docker-stop phoenix-start phoenix-stop docs setup develop

# Variables
PYTHON_INTERPRETER := python3
PIP_INSTALL := uv pip install
PYTEST := $(PYTHON_INTERPRETER) -m pytest
COVERAGE := $(PYTHON_INTERPRETER) -m pytest --cov=src/ru_twin --cov-report=html
FLAKE8 := $(PYTHON_INTERPRETER) -m flake8
MYPY := $(PYTHON_INTERPRETER) -m mypy
BLACK := $(PYTHON_INTERPRETER) -m black
ISORT := $(PYTHON_INTERPRETER) -m isort
DOCKER_COMPOSE := docker-compose
PHOENIX_PORT := 6006

help:
	@echo "Available commands:"
	@echo "  setup           - Set up development environment"
	@echo "  develop         - Install in development mode"
	@echo "  install         - Install dependencies"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  coverage        - Run tests with coverage report"
	@echo "  lint            - Run all linters"
	@echo "  format          - Format code using black and isort"
	@echo "  run             - Run the application"
	@echo "  clean           - Clean build artifacts and cache"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-run      - Run Docker container"
	@echo "  docker-stop     - Stop Docker container"
	@echo "  phoenix-start   - Start Arize Phoenix observability server"
	@echo "  phoenix-stop    - Stop Arize Phoenix observability server"
	@echo "  docs            - Generate documentation"

# Setup development environment
setup:
	@echo "Setting up development environment..."
	$(PYTHON_INTERPRETER) -m venv .venv
	. .venv/bin/activate && $(PIP_INSTALL) --upgrade pip uv
	. .venv/bin/activate && $(PIP_INSTALL) -r requirements-dev.txt
	. .venv/bin/activate && $(PIP_INSTALL) -r requirements.txt
	. .venv/bin/activate && $(PIP_INSTALL) -e .
	@echo "\nSetup complete! Activate the virtual environment with:"
	@echo "source .venv/bin/activate"

# Install in development mode
develop:
	. .venv/bin/activate && $(PIP_INSTALL) -e .

# Install dependencies
install:
	. .venv/bin/activate && $(PIP_INSTALL) -r requirements.txt

# Test commands
test:
	$(PYTEST) tests/

test-unit:
	$(PYTEST) tests/unit/

test-integration:
	$(PYTEST) tests/integration/

coverage:
	$(COVERAGE) tests/
	@echo "Coverage report generated at htmlcov/index.html"

# Linting and formatting
lint:
	$(FLAKE8) src/ru_twin tests/
	$(MYPY) src/ru_twin tests/

format:
	$(BLACK) src/ru_twin tests/
	$(ISORT) src/ru_twin tests/

# Run the application
run:
	$(PYTHON_INTERPRETER) -m ru_twin

# Clean up
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name "*.egg-info" -exec rm -r {} +
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/

# Docker commands
docker-build:
	$(DOCKER_COMPOSE) build

docker-run:
	$(DOCKER_COMPOSE) up -d

docker-stop:
	$(DOCKER_COMPOSE) down

# Phoenix observability
phoenix-start:
	@echo "Starting Phoenix server on port $(PHOENIX_PORT)"
	phoenix serve -p $(PHOENIX_PORT) &


phoenix-stop:
	@pkill -f "phoenix serve -p $(PHOENIX_PORT)" || true

# Documentation
docs:
	$(PYTHON_INTERPRETER) -m pdoc --html -o docs/ src/ru_twin
	@echo "Documentation generated in docs/ directory"

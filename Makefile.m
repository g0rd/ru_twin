SHELL := /bin/bash

.PHONY: help install test test-unit test-integration lint run build clean docker-build docker-run docker-stop phoenix-start phoenix-stop docs

# Variables
PYTHON_INTERPRETER := python3
PIP_INSTALL := $(PYTHON_INTERPRETER) -m pip install
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
	@echo "  install         - Install dependencies"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  coverage        - Run tests with coverage report"
	@echo "  lint            - Run all linters"
	@echo "  format          - Format code using black and isort"
	@echo "  run             - Run the application"
	@echo "  build           - Build the project (if applicable)"
	@echo "  clean           - Clean build artifacts and cache"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-run      - Run Docker container"
	@echo "  docker-stop     - Stop Docker container"
	@echo "  phoenix-start   - Start Arize Phoenix observability server"
	@echo "  phoenix-stop    - Stop Arize Phoenix observability server"
	@echo "  docs            - Generate documentation"

install:
	@echo "Installing dependencies..."
	$(PIP_INSTALL) -r requirements.txt
	# If using Poetry: poetry install

test: test-unit test-integration
	@echo "All tests completed."

test-unit:
	@echo "Running unit tests..."
	$(PYTEST) src/tests/unit/

test-integration:
	@echo "Running integration tests..."
	$(PYTEST) src/tests/integration/

coverage:
	@echo "Running tests with coverage..."
	$(COVERAGE)
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running linters..."
	$(FLAKE8) src/
	$(MYPY) src/
	$(BLACK) --check src/
	$(ISORT) --check src/

format:
	@echo "Formatting code..."
	$(BLACK) src/
	$(ISORT) src/

run:
	@echo "Running the application..."
	$(PYTHON_INTERPRETER) src/ru_twin/main.py

build:
	@echo "Building the project..."
	# Add build commands if your project requires a build step
	@echo "No build step configured."

clean:
	@echo "Cleaning up..."
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf .pytest_cache .coverage htmlcov build dist *.egg-info

docker-build:
	@echo "Building Docker image..."
	$(DOCKER_COMPOSE) build

docker-run:
	@echo "Running Docker containers..."
	$(DOCKER_COMPOSE) up -d

docker-stop:
	@echo "Stopping Docker containers..."
	$(DOCKER_COMPOSE) down

phoenix-start:
	@echo "Starting Arize Phoenix observability server on port $(PHOENIX_PORT)..."
	phoenix start --port $(PHOENIX_PORT)

phoenix-stop:
	@echo "Stopping Arize Phoenix observability server..."
	phoenix stop

docs:
	@echo "Generating documentation..."
	$(PYTHON_INTERPRETER) -m pdoc --html --output-dir docs/ src/ru_twin
	@echo "Documentation generated in docs/ru_twin/"

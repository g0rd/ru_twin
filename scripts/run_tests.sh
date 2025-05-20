#!/bin/bash
set -e

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run pytest with coverage
echo "Running tests with coverage..."
python -m pytest tests/ -v --cov=src/ru_twin --cov-report=term-missing

# Generate HTML coverage report
echo "Generating HTML coverage report..."
coverage html

echo "Coverage report generated at htmlcov/index.html"

#!/bin/bash
set -e

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run flake8
echo "Running flake8..."
flake8 src tests

# Run mypy
echo "Running mypy..."
mypy src

# Run black in check mode
echo "Running black in check mode..."
black --check src tests

# Run isort in check mode
echo "Running isort in check mode..."
isort --check-only src tests

echo "Linting complete! 🎯"

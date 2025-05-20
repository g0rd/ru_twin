#!/bin/bash
set -e

# Activate virtual environment if not already activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run isort
echo "Running isort..."
isort src tests

# Run black
echo "Running black..."
black src tests

echo "Formatting complete! ✨"

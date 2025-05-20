#!/bin/bash
set -e

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install uv
echo "Upgrading pip and installing uv..."
pip install --upgrade pip
pip install uv

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt
uv pip install -r requirements/dev.txt

# Install the package in development mode
echo "Installing package in development mode..."
pip install -e .

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

echo ""
echo "Setup complete! 🎉"
echo "Activate the virtual environment with:"
echo "source .venv/bin/activate"

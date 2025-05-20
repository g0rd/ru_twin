#!/bin/bash
set -e

echo "Cleaning up..."
find . -type d -name "__pycache__" -exec rm -r {} + || true
find . -type d -name "*.egg-info" -exec rm -r {} + || true
find . -type d -name ".pytest_cache" -exec rm -r {} + || true
find . -type d -name ".mypy_cache" -exec rm -r {} + || true
rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ || true
echo "Cleanup complete! 🧹"

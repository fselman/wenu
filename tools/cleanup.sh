#!/bin/bash

set -e

echo "Removing Python caches..."
find . -type d -name "__pycache__" -prune -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "Removing notebook checkpoints..."
find . -type d -name ".ipynb_checkpoints" -prune -exec rm -rf {} +

echo "Removing macOS metadata..."
find . -name ".DS_Store" -delete
find . -name "._*" -delete

echo "Removing build artifacts..."
rm -rf build dist
rm -rf .pytest_cache .mypy_cache .ruff_cache
find . -type d -name "*.egg-info" -prune -exec rm -rf {} +

echo "Finding files larger than 10 Mbytes"
find . -type f -size +10M -print

echo "Done."

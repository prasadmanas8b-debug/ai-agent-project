#!/bin/bash
# run_tests.sh — Run the full test suite with coverage report
# Usage: bash run_tests.sh

set -e

echo ""
echo "================================================="
echo "  AI Agent System — Test Suite"
echo "================================================="
echo ""

# Activate venv if it exists
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
  source venv/Scripts/activate
fi

# Install pytest and coverage if not present
pip install pytest pytest-cov --quiet

echo "Running tests..."
echo ""

# Run tests with coverage
python -m pytest tests/ \
  -v \
  --tb=short \
  --no-header \
  --cov=agents \
  --cov=tools \
  --cov=graph \
  --cov=config \
  --cov-report=term-missing \
  --cov-report=html:outputs/coverage_report \
  "$@"

echo ""
echo "Coverage report saved to outputs/coverage_report/index.html"

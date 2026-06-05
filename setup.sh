#!/bin/bash
# setup.sh — One-command environment setup for AI Agent System
# Usage: bash setup.sh

set -e

echo ""
echo "================================================="
echo "  AI Agent System — Setup"
echo "================================================="
echo ""

# Check Python version
PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
  echo "ERROR: Python 3.11+ is required but not found."
  exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python version: $PY_VERSION"

# Create virtual environment
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  $PYTHON -m venv venv
fi

# Activate venv
if [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
  source venv/Scripts/activate
fi

echo "Installing dependencies..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo ""

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
  echo "IMPORTANT: Edit .env and add your API keys before running!"
else
  echo ".env already exists — skipping"
fi

# Create outputs directory
mkdir -p outputs uploads

echo ""
echo "================================================="
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env and add your API keys"
echo "     - GROQ_API_KEY  (required) — console.groq.com"
echo "     - TAVILY_API_KEY (optional) — tavily.com"
echo "     - GITHUB_TOKEN   (optional) — github.com/settings/tokens"
echo "     - EMAIL_ADDRESS + EMAIL_PASSWORD (optional)"
echo ""
echo "  2. Run the system:"
echo "     python main.py"
echo ""
echo "  3. Or run the API server:"
echo "     uvicorn api.main:app --reload"
echo "================================================="

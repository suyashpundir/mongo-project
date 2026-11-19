#!/usr/bin/env bash
set -e

# Navigate to backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/backend"

echo "=== [NetPulse] Starting FastAPI Backend on Linux ==="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install it with: sudo apt install python3 python3-venv"
    exit 1
fi

# Create virtualenv if not exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment (.venv)..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install requirements
echo "Installing/verifying backend dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Start uvicorn
echo "Launching FastAPI Uvicorn server on http://0.0.0.0:8000 ..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

#!/usr/bin/env bash
set -e

# Navigate to frontend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"

echo "=== [NetPulse] Starting Vite React Dashboard on Linux ==="

# Check Node and npm
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js (v18+) and npm."
    exit 1
fi

# Install dependencies if node_modules missing
if [ ! -d "node_modules" ]; then
    echo "Installing frontend npm packages..."
    npm install
fi

echo "Launching Vite development server on http://localhost:5173 ..."
exec npm run dev -- --host 0.0.0.0

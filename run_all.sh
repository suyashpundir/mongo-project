#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "          ⚡ NetPulse Autonomous SRE Platform (Linux)        "
echo "============================================================"

# Ensure scripts are executable
chmod +x start_backend.sh start_frontend.sh seed_db.sh

# Function to kill child processes on exit
cleanup() {
    echo ""
    echo "[NetPulse] Stopping all services..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Start backend in background
./start_backend.sh &
BACKEND_PID=$!

# Wait for backend to initialize
echo "[NetPulse] Waiting for backend to warm up..."
sleep 3

# Start frontend
./start_frontend.sh &
FRONTEND_PID=$!

echo ""
echo "🚀 NetPulse is running!"
echo "   - Frontend Dashboard: http://localhost:5173"
echo "   - Backend API Docs:   http://localhost:8000/docs"
echo "   - WebSocket Stream:   ws://localhost:8000/ws/telemetry"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait for both processes
wait

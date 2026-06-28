#!/bin/bash
# One-command demo startup
# Starts: mock x402 server + agent + frontend

set -e

echo "=========================================="
echo "  YieldAgent Demo Startup"
echo "=========================================="
echo ""

# Check Python
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "Error: Node.js not found"
    exit 1
fi

# Install dependencies
echo "[1/4] Installing Python dependencies..."
pip install -q -r agent/requirements.txt -r mock_x402_server/requirements.txt 2>/dev/null

echo "[2/4] Installing Node dependencies..."
cd frontend && npm install --silent && cd ..

echo ""
echo "Starting services..."
echo ""

# Start mock x402 server
echo "[3/4] Starting mock x402 data source on :8000..."
cd mock_x402_server
python main.py &
MOCK_PID=$!
cd ..
sleep 2

# Start agent
echo "[4/4] Starting AI agent on :8080 (WebSocket)..."
cd agent
python main.py &
AGENT_PID=$!
cd ..
sleep 2

echo ""
echo "=========================================="
echo "  Services Running"
echo "=========================================="
echo ""
echo "  Mock x402:  http://localhost:8000"
echo "  Agent WS:   ws://localhost:8080"
echo ""
echo "  Starting frontend..."
echo ""

# Start frontend
cd frontend
npm run dev

# Cleanup on exit
trap "kill $MOCK_PID $AGENT_PID 2>/dev/null" EXIT

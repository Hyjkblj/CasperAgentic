@echo off
REM YieldAgent Demo Startup (Windows)
REM Starts: mock x402 server + agent + frontend

echo ==========================================
echo   YieldAgent Demo Startup
echo ==========================================
echo.

REM Install dependencies
echo [1/3] Installing Python dependencies...
pip install -q -r agent\requirements.txt -r mock_x402_server\requirements.txt 2>nul

echo [2/3] Installing Node dependencies...
cd frontend && npm install --silent && cd ..

echo.
echo Starting services...
echo.

REM Start mock x402 server
echo [3/3] Starting mock x402 data source on :8000...
start "Mock x402" cmd /c "cd mock_x402_server && python main.py"
timeout /t 2 >nul

REM Start agent
echo Starting AI agent on :8080 (WebSocket)...
start "Agent" cmd /c "cd agent && python main.py"
timeout /t 2 >nul

echo.
echo ==========================================
echo   Services Running
echo ==========================================
echo.
echo   Mock x402:  http://localhost:8000
echo   Agent WS:   ws://localhost:8080
echo.
echo   Starting frontend...
echo.

REM Start frontend
cd frontend && npm run dev

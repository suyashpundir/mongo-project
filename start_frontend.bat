@echo off
title NetPulse Frontend Dashboard
cd /d "%~dp0frontend"
echo [NetPulse] Starting Vite React Dashboard on http://localhost:5173 ...
call npm run dev
pause

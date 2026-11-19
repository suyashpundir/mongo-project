@echo off
title NetPulse Database Seeder
cd /d "%~dp0backend"
echo [NetPulse] Seeding historical incidents, runbooks, and telemetry into MongoDB...
call .venv\Scripts\python.exe seed_data.py
echo Database seeding complete!
pause

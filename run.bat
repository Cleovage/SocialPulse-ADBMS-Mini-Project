@echo off
title SocialPulse - ADBMS Social Media Analytics Platform
color 0B

echo =========================================================================
echo       SocialPulse: Social Media Trend ^& Influencer Analytics Platform
echo           Advanced Database Management System (ADBMS) Project
echo                     MongoDB Enterprise Engine
echo =========================================================================
echo.

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ and re-run this script.
    pause
    exit /b 1
)

:: 2. Check / Install Python Dependencies
echo [1/3] Checking Python dependencies...
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Encountered issues installing dependencies. Continuing...
)

:: 3. Seed Database & Ensure ADBMS Indexes
echo [2/3] Verifying MongoDB connection and seeding dataset...
python scripts/run_seeder.py
if %errorlevel% neq 0 (
    echo [ERROR] Failed to connect to MongoDB or seed database!
    echo Ensure MongoDB service is running on localhost:27017.
    pause
    exit /b 1
)

:: 4. Launch Application Server
echo [3/3] Starting FastAPI server on http://localhost:8000 ...
echo [i] Frontend Dashboard: http://localhost:8000
echo [i] OpenAPI Docs:       http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server at any time.
echo =========================================================================
echo.

:: Launch default browser
start "" "http://localhost:8000"

:: Start Uvicorn Server
python main.py

pause

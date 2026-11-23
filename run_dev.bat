@echo off
title GIKI Nexus - Full Stack Development Mode
echo ========================================================
echo        GIKI NEXUS - DEVELOPMENT MODE
echo Starting FastAPI Backend (8000) and Vite Frontend (5173)...
echo ========================================================
echo.
start "GIKI Nexus Backend" cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 2 >nul
start "GIKI Nexus Frontend" cmd /k "npm.cmd run dev --prefix frontend"
echo Both servers started!
echo Frontend Dev URL: http://localhost:5173
echo Backend API URL:  http://127.0.0.1:8000

@echo off
title GIKI Nexus - Web Application
echo ========================================================
echo               GIKI NEXUS PLATFORM
echo   Academic Discovery & Student Teammate Finder
echo ========================================================
echo.
echo Initializing database and starting server...
echo Access URL: http://127.0.0.1:8000
echo.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause

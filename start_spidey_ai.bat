@echo off
title Spidey AI Cloud Studio
cd /d "%~dp0"
echo ========================================================
echo   🕷️  SPIDEY AI // Cloud Studio & AI Video Creator
echo   Zero Local Ollama RAM / 0%% CPU / Google Drive Mode
echo ========================================================
echo.
echo Launching Spidey AI at http://localhost:8080 ...
start "" "http://localhost:8080"
python -B server.py
pause

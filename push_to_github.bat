@echo off
title Spidey AI - Push to GitHub
cd /d "G:\My Drive\Spidey-AI"

echo =======================================================
echo          🕷️ SPIDEY AI // GITHUB DEPLOYMENT
echo =======================================================
echo.
echo Your local Git repository is committed and ready!
echo.
echo 1. If you haven't created a repository on GitHub yet:
echo    Go to https://github.com/new
echo    Repository name: spidey-ai
echo    Set to Public, and do NOT check README or .gitignore
echo.
set /p REPO_URL="2. Paste your GitHub repo URL (e.g. https://github.com/YOUR_USER/spidey-ai.git): "

if "%REPO_URL%"=="" (
    echo.
    echo [ERROR] No URL entered. Exiting...
    pause
    exit /b
)

echo.
echo Linking remote to: %REPO_URL%
git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
git branch -M main

echo.
echo Pushing Spidey AI to GitHub...
echo (If prompted, click Sign in with Browser in the popup window)
echo.
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo  SUCCESS! Your Spidey AI repo is live on GitHub!
    echo =======================================================
) else (
    echo.
    echo [ERROR] Push failed. Please check your GitHub repository URL and permissions.
)
echo.
pause

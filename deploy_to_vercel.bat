@echo off
title Spidey AI - Deploy to Vercel
cd /d "G:\My Drive\Spidey-AI"

echo =======================================================
echo          🕷️ SPIDEY AI // VERCEL DEPLOYMENT
echo =======================================================
echo.
echo Checking Vercel CLI...
call vercel --version
echo.
echo Step 1: Logging in to Vercel...
echo (A browser tab will open for you to click Continue / Confirm)
echo.
call vercel login

echo.
echo Step 2: Deploying Spidey AI directly to Vercel Production...
echo.
call vercel --prod --yes

if %ERRORLEVEL% EQU 0 (
    echo.
    echo =======================================================
    echo  SUCCESS! Your Spidey AI is live worldwide on Vercel!
    echo =======================================================
) else (
    echo.
    echo [NOTE] If needed, you can also link your GitHub repo directly
    echo on https://vercel.com/new with 1 click!
)
echo.
pause

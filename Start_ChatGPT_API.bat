@echo off
title ChatGPT Local API Launcher (Static Domain)
color 0A

echo ===================================================
echo   ChatGPT Local OpenAI API Server Launcher 🚀
echo   Static Domain: https://tartness-plating-subside.ngrok-free.dev
echo ===================================================
echo.

echo [1/3] Cleaning up background browser & ngrok processes...
taskkill /F /IM chrome.exe 2>nul
taskkill /F /IM ngrok.exe 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Starting Local FastAPI Server (port 8008)...
cd /d "C:\Users\User\Documents\antigravity\focused-hopper"
start "1. ChatGPT Python API Server" cmd /k "python main.py"

echo Waiting for server startup...
timeout /t 5 /nobreak >nul

echo [3/3] Starting Ngrok Tunnel with Static Domain...
start "2. Ngrok Tunnel (Static Domain)" cmd /k ""C:\Users\User\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" http --url=tartness-plating-subside.ngrok-free.dev 8008"

echo.
echo ===================================================
echo   ✅ SUCCESS: All services launched!
echo   
echo   - Local Endpoint:  http://127.0.0.1:8008/v1
echo   - PERMANENT Base URL:  https://tartness-plating-subside.ngrok-free.dev/v1
echo ===================================================
echo.
pause

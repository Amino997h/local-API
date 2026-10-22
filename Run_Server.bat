@echo off
title ChatGPT Local API - Server Launcher 🚀
color 0A

echo ===================================================
echo   ChatGPT Local OpenAI API Server Launcher 🚀
echo ===================================================
echo.

:: 1. تنظيف أي عمليات سابقة عالقة
echo [1/3] Cleaning up existing background browser & ngrok processes...
taskkill /F /IM chrome.exe 2>nul
taskkill /F /IM ngrok.exe 2>nul
timeout /t 1 /nobreak >nul

:: 2. تشغيل سيرفر الـ API
echo [2/3] Starting Local FastAPI Server (port 8008)...
cd /d "%~dp0"
start "1. ChatGPT Python API Server" cmd /k "python main.py"

echo Waiting for server initialization...
timeout /t 4 /nobreak >nul

:: 3. فحص وتشغيل Ngrok إن وجد
echo [3/3] Checking Ngrok tunnel...
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    start "2. Ngrok Tunnel" cmd /k "ngrok http 8008"
    echo Ngrok started successfully!
) else if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" (
    start "2. Ngrok Tunnel (WinGet)" cmd /k ""%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe" http 8008"
    echo Ngrok started from WinGet location!
) else (
    echo.
    echo [INFO] Ngrok is not detected in PATH.
    echo Server is running locally on http://127.0.0.1:8008/v1
    echo If you need external access, install Ngrok and run: ngrok http 8008
)

echo.
echo ===================================================
echo   ✅ SUCCESS: Server is running!
echo   
echo   - Local Base URL: http://127.0.0.1:8008/v1
echo   - API Key:        sk-chatgpt-local-secret-key
echo   - Model:          gpt-4o
echo ===================================================
echo.
pause

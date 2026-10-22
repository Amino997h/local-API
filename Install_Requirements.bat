@echo off
title ChatGPT Local API - Easy Installer 📦
color 0B

echo ===================================================
echo   ChatGPT Local OpenAI API - Installation Setup 🚀
echo ===================================================
echo.

:: 1. التحقق من وجود بايثون
echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please download and install Python from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)
python --version

:: 2. ترقية pip
echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip

:: 3. تثبيت المكاتب المطلوبة
echo.
echo [3/4] Installing dependencies from requirements.txt...
cd /d "%~dp0"
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install requirements. Please check your internet connection.
    pause
    exit /b
)

:: 4. تثبيت متصفح Playwright
echo.
echo [4/4] Installing Playwright Chromium browser...
playwright install chromium
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Playwright browser setup encountered an issue. Trying again...
    python -m playwright install chromium
)

echo.
echo ===================================================
echo   ✅ Installation Completed Successfully! 🎉
echo.
echo   You can now launch the project anytime using:
echo   Run_Server.bat
echo ===================================================
echo.
pause

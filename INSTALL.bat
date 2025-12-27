@echo off
title WhatsApp Scheduler - Installation
color 0B

echo ============================================================
echo   WhatsApp Group Scheduler - Installation
echo ============================================================
echo.
echo   This will install all required dependencies...
echo.
echo ============================================================
echo.

echo [1/4] Checking Python installation...
python --version
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed!
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit
)

echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [3/4] Installing required packages...
pip install -r requirements.txt

echo.
echo [4/4] Installing ChromeDriver manager...
pip install webdriver-manager

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.
echo   Next steps:
echo   1. Get Groq API key from: https://console.groq.com/keys
echo   2. Get WhatsApp group invite link
echo   3. Double-click START_APP.bat
echo   4. Open browser to: http://localhost:5000
echo.
echo ============================================================
pause
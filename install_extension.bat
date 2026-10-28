@echo off
title Volume Booster Pro - Chrome Extension Loader
color 0e
cd /d "%~dp0"

echo ======================================================================
echo       VOLUME BOOSTER PRO - CHROME EXTENSION 1-CLICK LOADER
echo ======================================================================
echo.
echo This script helps you run the Volume Booster Pro Chrome Extension.
echo.
echo Option 1: Launch Google Chrome with extension pre-loaded
echo Option 2: Open Chrome Extensions management page (chrome://extensions)
echo Option 3: Start local Audio Test Lab (node server.js)
echo.

set /p choice="Enter your choice (1-3) [default: 1]: "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo [*] Finding Google Chrome...
    set "CHROME_PATH="
    if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
    if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" set "CHROME_PATH=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
    
    if "!CHROME_PATH!"=="" (
        echo [!] Chrome executable not found in standard paths.
        echo Opening extensions page instead...
        start chrome "chrome://extensions/"
    ) else (
        echo [*] Launching Chrome with Volume Booster Pro loaded...
        start "" "!CHROME_PATH!" --load-extension="%~dp0"
    )
    exit /b 0
)

if "%choice%"=="2" (
    echo [*] Opening chrome://extensions...
    start chrome "chrome://extensions/"
    echo.
    echo Steps:
    echo 1. Turn on "Developer mode" in the top right.
    echo 2. Click "Load unpacked" in the top left.
    echo 3. Select this folder: %~dp0
    echo.
    pause
    exit /b 0
)

if "%choice%"=="3" (
    echo [*] Starting Audio Test Lab on http://localhost:3000...
    node server.js
    exit /b 0
)


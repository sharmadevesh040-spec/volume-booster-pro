@echo off
setlocal
cd /d "%~dp0"
title Volume Booster Pro - Master Build Engine
color 0b

echo ======================================================================
echo           VOLUME BOOSTER PRO - MASTER PRODUCTION BUILD SCRIPT
echo ======================================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

python build_installer.py %*
if %errorlevel% neq 0 (
    echo.
    echo [!] Build exited with error code %errorlevel%.
    exit /b %errorlevel%
)

echo.
exit /b 0

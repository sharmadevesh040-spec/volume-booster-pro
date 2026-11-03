@echo off
setlocal
cd /d "%~dp0"
title Volume Booster Pro - Release Publisher
color 0a

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in PATH!
    pause
    exit /b 1
)

python publish_release.py %*
if %errorlevel% neq 0 (
    echo.
    echo [!] Publisher exited with code %errorlevel%.
    exit /b %errorlevel%
)

exit /b 0

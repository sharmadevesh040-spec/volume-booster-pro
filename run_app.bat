@echo off
title Volume Booster Pro
cd /d "%~dp0"

set "INSTALL_DIR=%LOCALAPPDATA%\Programs\VolumeBoosterPro"
set "INSTALLED_EXE=%INSTALL_DIR%\VolumeBoosterPro.exe"

if /i "%~1"=="--install" goto prompt_install
if /i "%~1"=="-i" goto prompt_install

:: If already running from within the installed folder, launch immediately
if /i "%~dp0"=="%INSTALL_DIR%\" (
    if exist "%INSTALLED_EXE%" (
        start "" "%INSTALLED_EXE%"
        exit /b 0
    )
)

:prompt_install
:: If not installed, ask user automatically via native Windows prompt
if not exist "%INSTALLED_EXE%" (
    echo [*] Checking installation status...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.Windows.Forms; $ans = [System.Windows.Forms.MessageBox]::Show('Volume Booster Pro is not installed on this PC.`n`nWould you like to install it now?`n`n• Adds Desktop shortcut`n• Adds Start Menu shortcut`n• Enables system-wide Equalizer APO engine`n• Safe, non-admin user install', 'Volume Booster Pro - Setup', [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question); if ($ans -eq [System.Windows.Forms.DialogResult]::Yes) { exit 1 } else { exit 0 }"
    if errorlevel 1 (
        echo [*] Starting automatic installation...
        call install.bat 1
        exit /b 0
    )
)

:: Launch the application
if exist "%INSTALLED_EXE%" (
    start "" "%INSTALLED_EXE%"
) else if exist "dist\VolumeBoosterPro\VolumeBoosterPro.exe" (
    start "" "dist\VolumeBoosterPro\VolumeBoosterPro.exe"
) else (
    start "" python main.py
)
exit /b 0

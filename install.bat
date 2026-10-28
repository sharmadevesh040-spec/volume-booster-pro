@echo off
setlocal enabledelayedexpansion
title Volume Booster Pro - 1-Click Installer
color 0b
cd /d "%~dp0"

cls
echo ======================================================================
echo           VOLUME BOOSTER PRO - WINDOWS INSTALLATION WIZARD
echo ======================================================================
echo.
echo  This installer will set up Volume Booster Pro on your PC:
echo   [+] Install to %%LOCALAPPDATA%%\Programs\VolumeBoosterPro
echo   [+] Create Desktop Shortcut
echo   [+] Create Windows Start Menu Shortcut
echo   [+] Configure Equalizer APO Kernel Engine
echo   [+] Register in Windows Add/Remove Programs
echo.
echo ======================================================================
echo.
echo Select an option:
echo   [1] Install to PC (Recommended)
echo   [2] Run Portable (Launch without installing)
echo   [3] Setup Equalizer APO Engine
echo   [4] Exit
echo.

set /p choice="Enter your choice (1-4) [default: 1]: "
if "%choice%"=="" set choice=1

if "%choice%"=="1" goto do_install
if "%choice%"=="2" goto do_portable
if "%choice%"=="3" goto do_apo
if "%choice%"=="4" exit /b 0

:do_install
echo.
echo [*] Checking environment...

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [*] Python detected. Ensuring dependencies are installed...
    python -m pip install -r requirements.txt --quiet
    echo [*] Running installer routine...
    python -c "from app.installer import install_to_system; s, t = install_to_system(); print('Installed to: ' + t if s else 'Failed: ' + str(t))"
) else (
    :: Fallback to compiled exe or PowerShell installer
    if exist "dist\VolumeBoosterPro\VolumeBoosterPro.exe" (
        echo [*] Standalone binary found. Deploying to Program directory...
        set "TARGET_DIR=%LOCALAPPDATA%\Programs\VolumeBoosterPro"
        if not exist "!TARGET_DIR!" mkdir "!TARGET_DIR!"
        xcopy /E /I /Y "dist\VolumeBoosterPro\*" "!TARGET_DIR!\" >nul
        
        :: Create Desktop and Start Menu shortcuts
        powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $ws = New-Object -ComObject WScript.Shell; $desk = $ws.SpecialFolders('Desktop'); $prog = $ws.SpecialFolders('Programs'); $target = [IO.Path]::Combine($env:LOCALAPPDATA, 'Programs', 'VolumeBoosterPro', 'VolumeBoosterPro.exe'); $work = [IO.Path]::Combine($env:LOCALAPPDATA, 'Programs', 'VolumeBoosterPro'); $icon = [IO.Path]::Combine($work, 'assets', 'icon.ico'); $d = $ws.CreateShortcut([IO.Path]::Combine($desk, 'Volume Booster Pro.lnk')); $d.TargetPath = $target; $d.WorkingDirectory = $work; if (Test-Path $icon) { $d.IconLocation = $icon }; $d.Save(); $s = $ws.CreateShortcut([IO.Path]::Combine($prog, 'Volume Booster Pro.lnk')); $s.TargetPath = $target; $s.WorkingDirectory = $work; if (Test-Path $icon) { $s.IconLocation = $icon }; $s.Save(); }"
        echo [*] Shortcuts created on Desktop and Start Menu.
    ) else (
        echo [ERROR] Neither Python nor dist\VolumeBoosterPro\VolumeBoosterPro.exe was found.
        pause
        exit /b 1
    )
)

echo.
echo ======================================================================
echo           INSTALLATION COMPLETED SUCCESSFULLY!
echo ======================================================================
echo.
echo You can now launch Volume Booster Pro anytime from:
echo   - Your Desktop shortcut
echo   - Your Windows Start Menu
echo.
echo Launching Volume Booster Pro now...
timeout /t 2 >nul

if exist "%LOCALAPPDATA%\Programs\VolumeBoosterPro\VolumeBoosterPro.exe" (
    start "" "%LOCALAPPDATA%\Programs\VolumeBoosterPro\VolumeBoosterPro.exe"
) else (
    start "" run_app.bat
)
exit /b 0

:do_portable
echo [*] Launching portable mode...
call run_app.bat
exit /b 0

:do_apo
echo.
echo [*] Opening Equalizer APO download page...
start "" "https://sourceforge.net/projects/equalizerapo/"
echo.
echo Please download and run the Equalizer APO installer, select your output
echo playback device (e.g. Speakers), and restart your PC.
echo.
pause
goto :eof


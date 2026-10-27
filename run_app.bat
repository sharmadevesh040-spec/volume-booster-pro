@echo off
title Volume Booster Pro - Windows Audio Enhancer
cd /d "%~dp0"

if exist "dist\VolumeBoosterPro\VolumeBoosterPro.exe" (
    start "" "dist\VolumeBoosterPro\VolumeBoosterPro.exe"
) else (
    start "" python main.py
)
exit

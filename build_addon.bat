@echo off
title Compilando Addon Blender (.zip)
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_addon.ps1" %*

echo.
pause

@echo off
title Compilando com Rojo (.rbxmx)
cd /d "%~dp0"
echo ========================================================
echo   Compilando Plugin Blender Animations com Rojo...
echo ========================================================
echo.

if exist "rojo.exe" (
    rojo.exe build plugin.project.json --output "%LOCALAPPDATA%\Roblox\Plugins\BlenderAnimations_Decals.rbxmx"
    echo.
    echo [OK] Plugin compilado com sucesso com o Rojo!
    echo Salvo em: %LOCALAPPDATA%\Roblox\Plugins\BlenderAnimations_Decals.rbxmx
) else (
    python build_plugin.py
)

echo.
echo ========================================================
echo   Pronto! Pode fechar esta janela.
echo ========================================================
pause

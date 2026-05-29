@echo off
chcp 65001 > nul
color 0A
cls

echo.
echo ════════════════════════════════════════════════════════════════
echo   🚀 DATACOM APP - DESKTOP
echo ════════════════════════════════════════════════════════════════
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ❌ Python não encontrado!
    pause
    exit /b 1
)

echo ⏳ Iniciando app...
echo.

REM Executa o app
python app_embutido.py

echo.
echo ✅ App fechado
pause

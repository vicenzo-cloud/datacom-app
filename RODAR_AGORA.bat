@echo off
chcp 65001 > nul
color 0A
cls

echo.
echo ════════════════════════════════════════════════
echo   🚀 DATACOM APP
echo ════════════════════════════════════════════════
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado!
    echo.
    echo Instale em: https://python.org/downloads
    pause
    exit /b 1
)

echo ⏳ Iniciando servidor...
echo.

REM Executa o app
python app_desktop_com_servidor.py

if errorlevel 1 (
    echo.
    echo ❌ Erro ao executar!
    echo.
    pause
)

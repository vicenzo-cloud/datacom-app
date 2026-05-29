@echo off
chcp 65001 > nul
color 0A
cls

echo.
echo ════════════════════════════════════════════════════════════════
echo   🚀 DATACOM APP - SERVIDOR LOCAL
echo ════════════════════════════════════════════════════════════════
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ❌ ERRO: Python não encontrado!
    echo.
    echo Você precisa instalar Python:
    echo 👉 https://python.org/downloads
    echo.
    echo IMPORTANTE:
    echo ✅ Durante a instalação, marque "Add Python to PATH"
    echo ✅ Reinicie o computador depois
    echo.
    pause
    exit /b 1
)

echo ⏳ Iniciando servidor...
echo.

REM Executa o servidor
python servidor_simples.py

if errorlevel 1 (
    color 0C
    echo.
    echo ❌ Erro ao executar o servidor
    pause
)

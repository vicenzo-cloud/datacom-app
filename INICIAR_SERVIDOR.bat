@echo off
chcp 65001 > nul
color 0A
cls

echo.
echo ════════════════════════════════════════════════════════════════
echo   🚀 SERVIDOR DATACOM APP
echo ════════════════════════════════════════════════════════════════
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ❌ ERRO: Python não encontrado!
    echo.
    echo Instale Python em:
    echo https://python.org/downloads
    echo.
    echo ✅ Marque "Add Python to PATH" durante a instalação
    echo.
    pause
    exit /b 1
)

REM Instala Flask se não tiver
echo ⏳ Verificando dependências...
pip list | find "Flask" >nul 2>&1
if errorlevel 1 (
    echo 📦 Instalando Flask...
    pip install Flask -q
    if errorlevel 1 (
        color 0C
        echo ❌ Erro ao instalar Flask
        pause
        exit /b 1
    )
)

echo.
echo ✅ Tudo pronto!
echo.
echo 🚀 Iniciando servidor...
echo.

REM Inicia o servidor
python servidor.py

pause

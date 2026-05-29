@echo off
chcp 65001 > nul
color 0F
cls

echo.
echo ════════════════════════════════════════════════
echo   🔍 DEBUG - Testando tudo
echo ════════════════════════════════════════════════
echo.

echo 1. Testando Python...
python --version
if errorlevel 1 (
    echo ❌ Python não funciona
    pause
    exit /b 1
)
echo ✅ Python OK
echo.

echo 2. Instalando pywebview...
pip install pywebview -q
if errorlevel 1 (
    echo ❌ Erro ao instalar pywebview
    pip install pywebview
    pause
    exit /b 1
)
echo ✅ pywebview instalado
echo.

echo 3. Testando import...
python -c "import webview; print('✅ webview importado com sucesso')"
if errorlevel 1 (
    echo ❌ Erro ao importar webview
    pause
    exit /b 1
)
echo.

echo 4. Rodando app_embutido.py...
python app_embutido.py

pause

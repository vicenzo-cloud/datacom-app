@echo off
chcp 65001 > nul
color 0F
cls

echo.
echo ════════════════════════════════════════════════
echo   🔍 Testando app_completo.py
echo ════════════════════════════════════════════════
echo.

python app_completo.py

if errorlevel 1 (
    echo.
    echo ❌ ERRO ao rodar app_completo.py
)

pause

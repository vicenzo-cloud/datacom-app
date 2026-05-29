@echo off
chcp 65001 > nul
color 0F
cls

echo.
echo ════════════════════════════════════════════════
echo   🔍 TESTE DE DIAGNÓSTICO
echo ════════════════════════════════════════════════
echo.

echo 1. Testando Python...
python --version
if errorlevel 1 goto erro_python
echo ✅ Python OK
echo.

echo 2. Testando pip...
pip --version
if errorlevel 1 goto erro_pip
echo ✅ pip OK
echo.

echo 3. Instalando Flask...
pip install Flask --quiet
if errorlevel 1 goto erro_flask
echo ✅ Flask instalado
echo.

echo 4. Testando servidor...
python -c "from flask import Flask; print('✅ Flask funciona!')"
if errorlevel 1 goto erro_import
echo.

echo ════════════════════════════════════════════════
echo ✅ TUDO OK! Servidor pronto para usar
echo ════════════════════════════════════════════════
echo.
pause
exit /b 0

:erro_python
color 0C
echo ❌ ERRO: Python não instalado ou não está no PATH
echo.
echo Solução:
echo 1. Instale Python: https://python.org/downloads
echo 2. IMPORTANTE: Marque "Add Python to PATH"
echo 3. Reinicie o computador
pause
exit /b 1

:erro_pip
color 0C
echo ❌ ERRO: pip não funciona
pause
exit /b 1

:erro_flask
color 0C
echo ❌ ERRO: Não consegui instalar Flask
echo.
echo Tente manualmente:
echo pip install Flask
pause
exit /b 1

:erro_import
color 0C
echo ❌ ERRO: Flask não importa
pause
exit /b 1

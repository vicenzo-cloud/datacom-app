$appPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $appPath

# Instala pywebview silenciosamente
Write-Host "Preparando app..." -ForegroundColor Green
python -m pip install pywebview -q

# Executa o app
python app_simples.py

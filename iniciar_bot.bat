@echo off
title LAZARUS - Bot de estado
cd /d "%~dp0"

echo.
echo   ============================================
echo     LAZARUS OPS - Bot de estado de Discord
echo   ============================================
echo.

if not exist "config_local.json" (
    echo   ERROR: falta config_local.json
    echo   Copia config_local.ejemplo.json y rellena el webhook.
    echo.
    pause
    exit /b 1
)

REM Evita arrancar una segunda instancia si ya esta corriendo.
powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*bot_local.py*' }; if ($p) { exit 1 } else { exit 0 }"
if errorlevel 1 (
    echo   El bot YA ESTABA CORRIENDO.
    echo   No se arranca otra copia.
    echo.
    REM Pausa sin depender de la consola: ping a la interfaz local.
    ping -n 5 127.0.0.1 >nul
    exit /b 0
)

echo   Arrancando...
start "" /b "C:\Python314\pythonw.exe" "%~dp0bot_local.py"

ping -n 5 127.0.0.1 >nul

REM Comprueba que sigue vivo pasados unos segundos.
powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*bot_local.py*' }; if ($p) { Write-Host '   BOT ACTIVO - actualizando Discord cada minuto' -ForegroundColor Green } else { Write-Host '   FALLO AL ARRANCAR - revisa bot.log' -ForegroundColor Red }"

echo.
echo   Para detenerlo: detener_bot.bat
echo.
ping -n 6 127.0.0.1 >nul

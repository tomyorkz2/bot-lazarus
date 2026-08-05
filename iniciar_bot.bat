@echo off
REM Arranca el bot de estado de LAZARUS en segundo plano, sin ventana.
REM Para detenerlo: detener_bot.bat

cd /d "%~dp0"

if not exist "config_local.json" (
    echo ERROR: falta config_local.json
    echo Copia config_local.ejemplo.json y rellena el webhook.
    pause
    exit /b 1
)

echo Arrancando el bot de estado de LAZARUS...
start "" /b "C:\Python314\pythonw.exe" "%~dp0bot_local.py"

timeout /t 3 /nobreak >nul
echo.
echo Bot arrancado. Comprueba bot.log para ver la actividad.
echo Para detenerlo, ejecuta detener_bot.bat
echo.
pause

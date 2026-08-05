@echo off
title LAZARUS - Detener bot
cd /d "%~dp0"

echo.
echo   ============================================
echo     LAZARUS OPS - Detener el bot
echo   ============================================
echo.

powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*bot_local.py*' }; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('   BOT DETENIDO (PID ' + $_.ProcessId + ')') -ForegroundColor Yellow } } else { Write-Host '   El bot no estaba corriendo.' -ForegroundColor DarkGray }"

echo.
echo   El mensaje de Discord se queda con el ultimo estado.
echo.
ping -n 5 127.0.0.1 >nul

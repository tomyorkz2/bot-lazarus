@echo off
title LAZARUS - Detener bot
cd /d "%~dp0"

echo.
echo   ============================================
echo     LAZARUS OPS - Detener el bot
echo   ============================================
echo.

REM Se usa el PID de bot.lock en vez de filtrar por linea de comandos:
REM un proceso elevado oculta su CommandLine a las sesiones normales, y por
REM eso un bot viejo llego a quedarse corriendo invisible.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$lock = Join-Path $PWD 'bot.lock';" ^
  "$objetivos = @();" ^
  "if (Test-Path $lock) { $p = (Get-Content $lock -Raw).Trim(); if ($p) { $objetivos += [int]$p } }" ^
  "Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*bot_local.py*' } | ForEach-Object { $objetivos += $_.ProcessId };" ^
  "$objetivos = $objetivos | Sort-Object -Unique;" ^
  "if (-not $objetivos) { Write-Host '   El bot no estaba corriendo.' -ForegroundColor DarkGray; exit }" ^
  "foreach ($id in $objetivos) {" ^
  "  $pr = Get-Process -Id $id -ErrorAction SilentlyContinue;" ^
  "  if (-not $pr) { continue }" ^
  "  try { Stop-Process -Id $id -Force -ErrorAction Stop; Write-Host ('   BOT DETENIDO (PID ' + $id + ')') -ForegroundColor Yellow }" ^
  "  catch { Write-Host ('   NO SE PUDO DETENER EL PID ' + $id) -ForegroundColor Red; Write-Host '   Es un proceso elevado. Cierralo desde el Administrador de tareas' -ForegroundColor Yellow; Write-Host '   o abre esta ventana como administrador.' -ForegroundColor Yellow }" ^
  "}" ^
  "if (Test-Path $lock) { Remove-Item $lock -Force -ErrorAction SilentlyContinue }"

echo.
echo   El mensaje de Discord se queda con el ultimo estado.
echo.
ping -n 5 127.0.0.1 >nul

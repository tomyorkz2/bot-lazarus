@echo off
REM Detiene el bot de estado de LAZARUS.

echo Buscando el proceso del bot...

powershell -NoProfile -Command "$p = Get-CimInstance Win32_Process -Filter \"Name='pythonw.exe'\" | Where-Object { $_.CommandLine -like '*bot_local.py*' }; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('  Detenido (PID ' + $_.ProcessId + ')') } } else { Write-Host '  El bot no estaba corriendo.' }"

echo.
pause

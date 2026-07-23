@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo === RemixZ: reemplazar launcher y arrancar interfaz nueva ===
taskkill /F /IM RemixZ_Cleaner_X.exe >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
timeout /t 2 /nobreak >nul

if exist "%~dp0_pending_update\RemixZ_Cleaner_X.exe" (
  copy /Y "%~dp0_pending_update\RemixZ_Cleaner_X.exe" "%~dp0RemixZ_Cleaner_X.exe"
  if exist "%~dp0_pending_update\_internal" xcopy /E /Y /I /Q "%~dp0_pending_update\_internal" "%~dp0_internal"
  echo disk-app-launcher> "%~dp0launcher_mode.flag"
  echo Launcher reemplazado desde _pending_update.
) else if exist "%~dp0RemixZ_Cleaner_X.exe" (
  echo No hay pending; se usa EXE actual.
)

if exist "%~dp0ejecutar_Cleaner_X.vbs" (
  wscript.exe "%~dp0ejecutar_Cleaner_X.vbs"
) else if exist "%~dp0RemixZ_Cleaner_X_App.py" (
  start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" "%~dp0RemixZ_Cleaner_X_App.py"
) else (
  start "" "%~dp0RemixZ_Cleaner_X.exe"
)
exit /b 0

@echo off
setlocal EnableExtensions
cd /d "%~dp0"

REM 1) Aplicar launcher pendiente si existe (reemplazo definitivo del EXE viejo)
if exist "%~dp0_pending_update\RemixZ_Cleaner_X.exe" (
  echo Aplicando launcher nuevo...
  taskkill /F /IM RemixZ_Cleaner_X.exe >nul 2>&1
  timeout /t 1 /nobreak >nul
  copy /Y "%~dp0_pending_update\RemixZ_Cleaner_X.exe" "%~dp0RemixZ_Cleaner_X.exe" >nul
  if exist "%~dp0_pending_update\_internal" (
    xcopy /E /Y /I /Q "%~dp0_pending_update\_internal" "%~dp0_internal" >nul
  )
  echo disk-app-launcher> "%~dp0launcher_mode.flag"
)

REM 2) Si EXE es launcher (<2.2MB) usarlo; si no, App.py
set EXE=%~dp0RemixZ_Cleaner_X.exe
set APP=%~dp0RemixZ_Cleaner_X_App.py
set PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe
if not exist "%PYW%" set PYW=%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe
if not exist "%PYW%" set PYW=pythonw.exe

if exist "%EXE%" (
  for %%A in ("%EXE%") do set SIZE=%%~zA
)
if defined SIZE if %SIZE% LSS 2200000 (
  start "" "%EXE%"
  exit /b 0
)

if exist "%APP%" (
  start "" "%PYW%" "%APP%"
  exit /b 0
)

if exist "%EXE%" start "" "%EXE%"
exit /b 0

@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ========================================================
echo  RemixZ Cleaner X — compilar LAUNCHER (stdlib completa)
echo ========================================================
echo  Entrada: launcher.py
echo  Salida:  dist\launcher\RemixZ_Cleaner_X.exe + _internal
echo  Incluye: json, ssl, zipfile, urllib, tkinter (hiddenimports)
echo ========================================================
echo.

set ICON=icono.ico
if not exist "%ICON%" set ICON=payload\icono.ico
if not exist "%ICON%" (
  echo AVISO: sin icono.ico
  set ICON_ARG=
) else (
  set ICON_ARG=--icon "%ICON%"
)

set CTK=
if exist "lib\customtkinter" set CTK=--add-data "lib\customtkinter;customtkinter/"
if exist "payload\lib\customtkinter" if not defined CTK set CTK=--add-data "payload\lib\customtkinter;customtkinter/"

where pyinstaller >nul 2>&1
if errorlevel 1 (
  echo ERROR: pyinstaller no esta en PATH.
  echo   pip install pyinstaller
  exit /b 1
)

echo Compilando launcher.py con hiddenimports stdlib...
pyinstaller --noconfirm --onedir --windowed --uac-admin %ICON_ARG% %CTK% ^
  --name RemixZ_Cleaner_X ^
  --hidden-import=json ^
  --hidden-import=ssl ^
  --hidden-import=zipfile ^
  --hidden-import=urllib ^
  --hidden-import=urllib.request ^
  --hidden-import=urllib.error ^
  --hidden-import=urllib.parse ^
  --hidden-import=http ^
  --hidden-import=http.client ^
  --hidden-import=email ^
  --hidden-import=email.parser ^
  --hidden-import=dataclasses ^
  --hidden-import=threading ^
  --hidden-import=tempfile ^
  --hidden-import=shutil ^
  --hidden-import=hashlib ^
  --hidden-import=base64 ^
  --hidden-import=platform ^
  --hidden-import=copy ^
  --hidden-import=collections ^
  --hidden-import=concurrent.futures ^
  --hidden-import=tkinter ^
  --hidden-import=tkinter.filedialog ^
  --hidden-import=tkinter.ttk ^
  --hidden-import=tkinter.scrolledtext ^
  --hidden-import=tkinter.messagebox ^
  --hidden-import=importlib ^
  --hidden-import=importlib.util ^
  --collect-all tkinter ^
  "launcher.py"

if errorlevel 1 (
  echo FALLO pyinstaller
  exit /b 1
)

echo.
echo Listo: dist\RemixZ_Cleaner_X\RemixZ_Cleaner_X.exe
echo Copia el .exe + _internal junto a RemixZ_Cleaner_X_App.py
echo.
endlocal

@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ========================================================
echo  RemixZ Cleaner X — compilar LAUNCHER a EXE (onedir)
echo ========================================================
echo  Entrada: launcher.py
echo  Salida:  dist\launcher\launcher.exe
echo  (renombrar a RemixZ_Cleaner_X.exe y copiar junto a payload)
echo ========================================================
echo.

set ICON=payload\icono.ico
if not exist "%ICON%" set ICON=icono.ico
if not exist "%ICON%" (
  echo AVISO: no se encontro icono.ico — se compila sin icono custom
  set ICON_ARG=
) else (
  set ICON_ARG=--icon "%ICON%"
)

set CTK=
if exist "payload\lib\customtkinter" set CTK=--add-data "payload\lib\customtkinter;customtkinter/"
if exist "lib\customtkinter" if not defined CTK set CTK=--add-data "lib\customtkinter;customtkinter/"

where pyinstaller >nul 2>&1
if errorlevel 1 (
  echo ERROR: pyinstaller no esta en PATH.
  echo   pip install pyinstaller
  pause
  exit /b 1
)

echo Compilando launcher.py ...
pyinstaller --noconfirm --onedir --windowed --uac-admin %ICON_ARG% %CTK% "launcher.py"
if errorlevel 1 (
  echo FALLO pyinstaller
  pause
  exit /b 1
)

echo.
echo Listo: dist\launcher\launcher.exe
echo.
echo Pasos:
echo  1) Copia dist\launcher\*  -o-  solo launcher.exe + _internal del build
echo  2) Renombra launcher.exe a RemixZ_Cleaner_X.exe
echo  3) Coloca el .exe en la carpeta del payload (junto a RemixZ_Cleaner_X_App.py)
echo  4) NO borres RemixZ_Cleaner_X_App.py ni lib\ — el launcher los lee del disco
echo.
pause
endlocal

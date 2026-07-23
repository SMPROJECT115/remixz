' RemixZ Cleaner X — arranque DEFINITIVO
' 1) Aplica launcher pendiente (_pending_update) si existe
' 2) Si el .exe es el LAUNCHER nuevo (< 2.2 MB), lo usa
' 3) Si no, pythonw + App.py (interfaz nueva en disco)
' Así el cliente NUNCA se queda con la UI frozen del EXE viejo.
Option Explicit
Dim sh, fso, dir, exe, pendingExe, pendingInt, pyw, py, appPy, flag, size

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = dir

exe = dir & "\RemixZ_Cleaner_X.exe"
pendingExe = dir & "\_pending_update\RemixZ_Cleaner_X.exe"
pendingInt = dir & "\_pending_update\_internal"
appPy = dir & "\RemixZ_Cleaner_X_App.py"
flag = dir & "\launcher_mode.flag"

' --- 1) Aplicar launcher pendiente (EXE no está en uso si abrimos por VBS) ---
On Error Resume Next
If fso.FileExists(pendingExe) Then
  fso.CopyFile pendingExe, exe, True
  If fso.FolderExists(pendingInt) Then
    If Not fso.FolderExists(dir & "\_internal") Then fso.CreateFolder dir & "\_internal"
    ' xcopy via shell for nested runtime
    sh.Run "cmd.exe /c xcopy /E /Y /I /Q """ & pendingInt & """ """ & dir & "\_internal""", 0, True
  End If
  Dim ts
  ts = fso.OpenTextFile(flag, 2, True)
  ts.WriteLine "disk-app-launcher"
  ts.Close
End If
On Error GoTo 0

' --- 2) Elegir cómo arrancar ---
On Error Resume Next
size = 0
If fso.FileExists(exe) Then size = fso.GetFile(exe).Size
On Error GoTo 0

' Launcher nuevo ~1.6MB; EXE frozen viejo ~2.8MB+
If fso.FileExists(exe) And size > 0 And size < 2200000 Then
  sh.Run """" & exe & """", 1, False
  WScript.Quit 0
End If

' --- 3) Fallback: App.py en disco (siempre interfaz actualizable) ---
pyw = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python312\pythonw.exe"
If Not fso.FileExists(pyw) Then pyw = sh.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Programs\Python\Python311\pythonw.exe"
If Not fso.FileExists(pyw) Then pyw = "pythonw.exe"

If fso.FileExists(appPy) Then
  sh.Run """" & pyw & """ """ & appPy & """", 0, False
Else
  If fso.FileExists(exe) Then sh.Run """" & exe & """", 1, False
End If

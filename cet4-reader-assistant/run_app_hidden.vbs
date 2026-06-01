Option Explicit

Dim fso, shell, projectDir, runtimeDir, logPath, command, pythonw, launcher

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
runtimeDir = fso.BuildPath(projectDir, "runtime")
logPath = fso.BuildPath(runtimeDir, "launcher.log")

If Not fso.FolderExists(runtimeDir) Then
    fso.CreateFolder(runtimeDir)
End If

shell.CurrentDirectory = projectDir

pythonw = fso.BuildPath(projectDir, ".venv\Scripts\pythonw.exe")
launcher = fso.BuildPath(projectDir, "run_app_launcher.pyw")

If fso.FileExists(pythonw) Then
    command = Quote(pythonw) & " " & Quote(launcher)
Else
    command = shell.ExpandEnvironmentStrings("%ComSpec%") & " /d /c " & Quote(Quote(fso.BuildPath(projectDir, "run_app_logged.cmd")))
End If

shell.Run command, 0, False

Function Quote(value)
    Quote = Chr(34) & value & Chr(34)
End Function

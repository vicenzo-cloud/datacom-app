Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strPython = "python"

' Executa Python sem mostrar CMD
objShell.Run strPython & " """ & strPath & "\app_webview.py""", 0, False

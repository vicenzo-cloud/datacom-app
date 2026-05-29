Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Primeiro instala pywebview
objShell.Run "cmd /c python -m pip install pywebview -q", 0, True

' Depois executa o app sem CMD
objShell.Run "cmd /c python """ & strPath & "\app_webview.py""", 0, False

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Pega o caminho da pasta
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Instala pywebview se não tiver
objShell.Run "python -m pip install pywebview -q", 0, True

' Executa o app SEM mostrar a janela do CMD
objShell.Run "python """ & strPath & "\app_desktop.py""", 0, False

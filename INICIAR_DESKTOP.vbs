Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Executa Python em background (sem mostrar CMD)
objShell.Run "python """ & strPath & "\app_desktop_com_servidor.py""", 0, False

' Mostra mensagem
WScript.Sleep 2000
MsgBox "Datacom App iniciado!" & vbCrLf & vbCrLf & _
        "Seu navegador abrirá em alguns segundos." & vbCrLf & vbCrLf & _
        "Para fechar: feche esta janela ou o navegador.", 64, "Datacom App"

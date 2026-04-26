Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
pythonw = "C:\Users\Huawei\AppData\Local\Programs\Python\Python311\pythonw.exe"

If Not fso.FileExists(pythonw) Then
    pythonw = "pythonw"
End If

cmd = """" & pythonw & """ -X utf8 """ & baseDir & "\run_gateway_daemon.py"""
shell.Run cmd, 0, False

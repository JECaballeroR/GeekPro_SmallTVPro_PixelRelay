Set shell = CreateObject("WScript.Shell")
project = CreateObject("Scripting.FileSystemObject").GetParentFolderName( _
    CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName))
shell.CurrentDirectory = project
shell.Run "pyw -m pixel_relay tray", 0, False

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this VBS script is located
strScriptPath = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the App directory and run the Python application
objShell.CurrentDirectory = strScriptPath
objShell.Run "cmd /c py -m core.gui.main_qt", 0, False

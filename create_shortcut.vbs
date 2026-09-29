Set oWS = WScript.CreateObject("WScript.Shell")
Set oEnv = oWS.Environment("PROCESS")
sLinkFile = oEnv("USERPROFILE") & "\Desktop\Sume.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "C:\Users\Bernardo Jonas\sume\run_sume.bat"
oLink.WorkingDirectory = "C:\Users\Bernardo Jonas\sume"
oLink.Save
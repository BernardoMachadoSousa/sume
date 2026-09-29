$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut("$env:USERPROFILE\Desktop\Sume.lnk")
$shortcut.TargetPath = "python"
$shortcut.Arguments = '\"C:\Users\Bernardo Jonas\sume\main.py\"'
$shortcut.WorkingDirectory = "C:\Users\Bernardo Jonas\sume"
$shortcut.IconLocation = "%SystemRoot%\System32\imageres.dll,3"
$shortcut.Save()
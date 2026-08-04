$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$startup = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startup "Pixel Relay.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "wscript.exe"
$shortcut.Arguments = "`"$projectRoot\scripts\run_tray.vbs`""
$shortcut.WorkingDirectory = $projectRoot
$shortcut.Description = "Pixel Relay - Windows system tray"
$shortcut.Save()

Write-Host "Acceso de inicio creado en: $shortcutPath"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envPath = Join-Path $projectRoot ".env"

$deviceIp = Read-Host "GeekMagic IP [192.168.1.63]"
if ([string]::IsNullOrWhiteSpace($deviceIp)) {
    $deviceIp = "192.168.1.63"
}

$calendarUrl = Read-Host "Private Google Calendar ICS URL (optional)"

$content = @"
PIXEL_DEVICE_IP=$deviceIp
PIXEL_REQUEST_TIMEOUT=25
PIXEL_AUTO_ROTATION_ENABLED=true
PIXEL_ROTATION_SECONDS=5
PIXEL_MUSIC_FOCUS_ON_CHANGE=true
PIXEL_MUSIC_PAUSE_AUTOPLAY_ON_FOCUS=true
PIXEL_MUSIC_FOCUS_SECONDS=10
PIXEL_ROTATE_WHILE_PLAYING=true
PIXEL_MUSIC_ENABLED=true
PIXEL_FX_ENABLED=true
PIXEL_WEATHER_ENABLED=true
PIXEL_CALENDAR_ENABLED=true
PIXEL_CLOCK_ENABLED=true
PIXEL_NOTIFICATIONS_ENABLED=true
PIXEL_WEATHER_CITY=Rovaniemi
PIXEL_WEATHER_COUNTRY_CODE=FI
PIXEL_CALENDAR_ICS_URL="$calendarUrl"
PIXEL_NOTIFICATION_TITLE="THANK YOU"
PIXEL_NOTIFICATION_BODY="Thanks for using Pixel Relay."
PIXEL_NOTIFICATION_FOOTER="JECR"
PIXEL_NOTIFICATION_ACCENT="#1388e9"
PIXEL_TRAY_AUTOSTART=true
"@

$content.Trim() | Set-Content -Path $envPath -Encoding UTF8
Write-Host ""
Write-Host "Local configuration created at: $envPath"
Write-Host "This file is excluded by .gitignore."

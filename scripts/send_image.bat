@echo off
setlocal
cd /d "%~dp0\.."

if "%~1"=="" (
  echo Usage: scripts\send_image.bat path\image.jpg [remote_name.jpg]
  exit /b 1
)

if "%~2"=="" (
  py -m pixel_relay send "%~1"
) else (
  py -m pixel_relay send "%~1" --name "%~2"
)

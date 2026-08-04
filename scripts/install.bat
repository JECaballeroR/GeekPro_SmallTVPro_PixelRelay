@echo off
setlocal
cd /d "%~dp0\.."
if not exist ".env" copy ".env.example" ".env" >nul
py -m pip install --upgrade pip
py -m pip install -e .
echo.
echo Instalacion completada.
pause

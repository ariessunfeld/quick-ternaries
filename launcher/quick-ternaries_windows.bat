@echo off
SETLOCAL

:: Get the directory where the script is located
for %%I in ("%~dp0") do set "DIR=%%~fI"

:: Change directory to the script location
cd /d "%DIR%"

:: Check if virtual environment exists
IF NOT EXIST ".venv" (
    echo No virtual environment found; creating one...
    python3.11 -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) ELSE (
    echo Found a virtual environment; activating it...
    call .venv\Scripts\activate.bat
)

:: Start the updater
echo Checking for updates...
python updater.py

quick-ternaries

ENDLOCAL
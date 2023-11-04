@echo off

REM Get the directory where the script is located
SET "DIR=%~dp0"

REM Change directory to the script location
cd /d "%DIR%"

REM Check if virtual environment called ".venv" exists in the current directory or one level up
if not exist ".venv\" (
  if exist "..\.venv\" (
    REM If .venv exists one level up
    echo Activating virtual environment...
    call "..\.venv\Scripts\activate.bat"
  ) else (
    REM If .venv doesn't exist either in the current directory or one level up
    echo Setting up virtual environment...
    python -m venv .venv > NUL
    call ".venv\Scripts\activate.bat"
    echo Installing dependencies...
    pip install -r requirements.txt > NUL
  )
) else (
  REM If .venv exists in the current directory
  echo Activating virtual environment...
  call ".venv\Scripts\activate.bat"
)

REM Start the updater
echo Checking for updates...
python updater.py

REM After updates, run the main program
echo Launching Quick Ternaries...

REM Silence QT Logging from Terminal output
SET "QT_LOGGING_RULES=*.debug=false; qt.*.debug=false"

REM Filter output, assuming quick-ternaries is an executable in the PATH
quick-ternaries 2>&1 | findstr /v /c:"synchronize] called within transaction" /c:"unrecognized selector sent to instance"

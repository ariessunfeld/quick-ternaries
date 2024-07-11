@echo off
:: Locate the Conda installation directory
for /f "delims=" %%i in ('conda info --base') do set CONDA_BASE=%%i

:: Check if CONDA_BASE was set correctly
if not defined CONDA_BASE (
    echo Conda base directory not found.
    pause
    exit /b 1
)

:: Construct the command to activate the environment and execute the additional commands
set CMD="call \"%CONDA_BASE%\condabin\conda.bat\" activate quick_ternaries ^&^& echo Checking for updates... ^&^& python updater.py ^&^& echo Launching Quick Ternaries... (please keep this window open) ^&^& set QT_LOGGING_RULES=*.debug=false;qt.*.debug=false ^&^& quick-ternaries 2>&1 | findstr /V \"synchronize] called within transaction\|unrecognized selector sent to instance\" ^&^& pause"

:: Start Anaconda Prompt and execute the commands
start "Anaconda Prompt" "%CONDA_BASE%\Scripts\activate.bat" "%CMD%"

:: Pause to keep the window open if something goes wrong before starting the Anaconda Prompt
pause


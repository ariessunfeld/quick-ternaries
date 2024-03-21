@echo off
setlocal

:: Define your Conda environment name
set "ENV_NAME=quick_ternaries"

:: Assume this script is located in the same directory as your Python script and environment.yml
:: Get the directory where the script is located
set "DIR=%~dp0"

:: Navigate to the script directory
cd /d "%DIR%"

:: Check if the Conda environment exists
call conda info --envs | findstr /C:"%ENV_NAME%" > nul
if errorlevel 1 (
    echo Conda environment '%ENV_NAME%' does not exist. Creating now...
    call conda env create -f environment.yml
) else (
    echo Conda environment '%ENV_NAME%' exists.
)

:: Activate the environment
echo Activating the '%ENV_NAME%' environment...
call conda activate %ENV_NAME%

:: Run the Python script
call python updater.py

:: Launch quick-ternaries tool
echo Launching Quick Ternaries... (please keep this window open)
call quick-ternaries


@echo off
setlocal

if not exist quickternaries_config.bat (
    echo ERROR: quickternaries_config.bat not found.
    echo Please run setup.bat from an Anaconda Prompt first.
    pause
    exit /b 1
)

if not exist environment.yml (
    echo ERROR: environment.yml not found.
    pause
    exit /b 1
)

call quickternaries_config.bat

set "ENV_NAME=quick_ternaries"

echo Checking for Conda environment "%ENV_NAME%"...
call "%CONDA_BASE%\condabin\conda.bat" run -n %ENV_NAME% python --version >nul 2>nul
if errorlevel 1 (
    echo Environment "%ENV_NAME%" not found. Creating it from environment.yml...
    call "%CONDA_BASE%\condabin\conda.bat" env create -f environment.yml
    if errorlevel 1 (
        echo ERROR: Failed to create Conda environment.
        pause
        exit /b 1
    )
) else (
    echo Environment "%ENV_NAME%" exists.
)

echo.
echo Activating Conda environment "%ENV_NAME%"...
call "%CONDA_BASE%\condabin\conda.bat" activate %ENV_NAME%
if errorlevel 1 (
    echo ERROR: Failed to activate Conda environment.
    pause
    exit /b 1
)

echo.
echo Validating Python version...
python -c "import sys; raise SystemExit(not ((3, 11) <= sys.version_info[:2] < (3, 15)))"
if errorlevel 1 (
    echo ERROR: Quick Ternaries requires Python 3.11, 3.12, 3.13, or 3.14.
    pause
    exit /b 1
)

echo.
echo Ensuring updater dependencies are installed...
python -m pip install "requests>=2.31,<3"
if errorlevel 1 (
    echo ERROR: Failed to install updater dependencies.
    pause
    exit /b 1
)

echo.
echo Running updater...
python updater.py
if errorlevel 1 (
    echo ERROR: Updater failed.
    pause
    exit /b 1
)

echo.
echo Launching Quick Ternaries... (please keep this window open)
quick-ternaries
pause

endlocal

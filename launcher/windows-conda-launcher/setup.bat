@echo off
setlocal

:: setup.bat must be run from an Anaconda Prompt.

for /f "delims=" %%i in ('conda info --base') do set "CONDA_BASE=%%i"
if not defined CONDA_BASE (
    echo ERROR: Could not find the Conda base environment.
    echo Please run this setup script from an Anaconda Prompt.
    pause
    exit /b 1
)

echo Found Conda base at: %CONDA_BASE%

>quickternaries_config.bat echo set "CONDA_BASE=%CONDA_BASE%"
echo Configuration file quickternaries_config.bat has been updated.

if not exist TemplateLauncher.bat (
    echo ERROR: Launcher template "TemplateLauncher.bat" not found.
    pause
    exit /b 1
)

if not exist environment.yml (
    echo ERROR: Conda environment file "environment.yml" not found.
    pause
    exit /b 1
)

copy /Y TemplateLauncher.bat RunQuickTernaries.bat
if errorlevel 1 (
    echo ERROR: Failed to create RunQuickTernaries.bat.
    pause
    exit /b 1
)

echo RunQuickTernaries.bat has been created.
echo You can now double-click RunQuickTernaries.bat to launch Quick Ternaries and check for updates.
pause

endlocal

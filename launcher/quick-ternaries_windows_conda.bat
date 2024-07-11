@echo off

REM Get the directory of the batch file
set BATCH_FILE_DIR=%~dp0

REM Command to create and activate the environment, and run the updater script
set CREATE_AND_ACTIVATE_ENV=cd /d "%BATCH_FILE_DIR%" ^&^& conda env create -f environment.yml ^&^& echo Activating Quick Ternaries environment ^&^& conda activate quick_ternaries ^&^& echo Checking for updates... ^&^& python updater.py ^&^& echo Launching Quick Ternaries... (please keep this window open) ^&^& quick-ternaries

REM Start Anaconda Prompt and run the commands
start "Anaconda Prompt" cmd.exe /K "%CREATE_AND_ACTIVATE_ENV% ^&^& pause"

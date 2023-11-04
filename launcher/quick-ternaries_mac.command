#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change directory to the script location
cd "$DIR"

# Check if virtual environment called ".venv" exists in the current directory or one level up
if [ ! -d ".venv" ]; then
  if [ -d "../.venv" ]; then
    # If .venv exists one level up
    echo "Activating virtual environment..."
    source ../.venv/bin/activate
  else
    # If .venv doesn't exist either in the current directory or one level up
    echo "Setting up virtual environment..."
    python3.11 -m venv .venv > /dev/null
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt > /dev/null
  fi
else
  # If .venv exists in the current directory
  echo "Activating virtual environment..."
  source .venv/bin/activate
fi

# Start the updater
echo "Checking for updates..."
python updater.py

# After updates, run the main program
echo "Launching Quick Ternaries..."

# Silence QT Logging from Terminal output
export QT_LOGGING_RULES='*.debug=false; qt.*.debug=false'

quick-ternaries 2>&1 | grep -vE "(synchronize] called within transaction|unrecognized selector sent to instance)"

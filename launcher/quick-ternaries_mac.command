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
    PYTHON_BIN=""
    for candidate in python3.14 python3.13 python3.12 python3.11; do
      if command -v "$candidate" > /dev/null 2>&1; then
        PYTHON_BIN="$candidate"
        break
      fi
    done
    if [ -z "$PYTHON_BIN" ]; then
      echo "Python 3.11, 3.12, 3.13, or 3.14 is required but was not found."
      exit 1
    fi
    "$PYTHON_BIN" -m venv .venv > /dev/null
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
echo "Launching Quick Ternaries... (please keep this window open)"

# Silence QT Logging from Terminal output
export QT_LOGGING_RULES='*.debug=false; qt.*.debug=false'

quick-ternaries 2>&1 | grep -vE "(synchronize] called within transaction|unrecognized selector sent to instance)"

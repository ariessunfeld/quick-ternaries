#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change directory to the script location
cd $DIR

# Check if virtual environment called ".venv" exists in the current directory or one level up
if [ ! -d ".venv" ]; then
  if [ -d "../.venv" ]; then
    # If .venv exists one level up
    source ../.venv/bin/activate
  else
    # If .venv doesn't exist either in the current directory or one level up
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
  fi
else
  # If .venv exists in the current directory
  source .venv/bin/activate
fi


# Start the updater
python updater.py

# After updates, run the main program
quick-ternaries

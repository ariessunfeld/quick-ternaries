#!/bin/bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change directory to the script location
cd $DIR

# Check if virtual environment called ".venv" exists
if [ ! -d ".venv" ]; then
  python3.11 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

# Start the updater
python updater.py

# After updates, run the main program
quick-ternaries

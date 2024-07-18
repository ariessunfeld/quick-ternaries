#!/bin/bash

# Define your Conda environment name
ENV_NAME="quick_ternaries"

# Assume this script is located in the same directory as your Python script and environment.yml
# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Navigate to the script directory
cd $DIR

# Path to the environment.yml file
ENV_YML_PATH="${DIR}/environment.yml"

# Check if the Conda environment exists
if ! conda info --envs | grep $ENV_NAME > /dev/null; then
    echo "Conda environment '$ENV_NAME' does not exist. Creating now... (this may take a couple minutes)"
    # conda deactivate
    conda env create -f "$ENV_YML_PATH"
else
    echo "Conda environment '$ENV_NAME' exists."
fi

# Activate the environment
echo "Activating the '$ENV_NAME' environment..."
eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

# Run the Python script
# python3 "${DIR}/updater.py"

# Dynamically get the path to the Conda 'bin' directory
PYTHON_BIN="$(conda info --base)/envs/$ENV_NAME/bin"

# Run the Python script using the Python executable within the Conda environment
"$PYTHON_BIN/python3" "${DIR}/updater.py"

# Launch quick-ternaries tool
echo "Launching Quick Ternaries... (please keep this window open)"

quick-ternaries

"""Script to create a new virtual environment and install dependencies from 
a requirements.txt file"""

import os
import sys
import subprocess
import platform

def ensure_venv():
    # The path of the virtual environment you want to check.
    # You may want to customize this.
    venv_path = os.path.abspath('venv')

    # Get the path of the active virtual environment.
    active_venv_path = os.getenv('VIRTUAL_ENV')

    if active_venv_path is None:
        sys.exit("Error: no virtual environment active. "
                 "Please activate the virtual environment before running this script.\n"
                 "To create a virtual environment, run:\n\npython setup_venv.py\n")
    elif os.path.normcase(os.path.abspath(active_venv_path)) != os.path.normcase(venv_path):
        sys.exit(f"Error: the wrong virtual environment is active. "
                 f"Expected {venv_path}, but {active_venv_path} is active. "
                 "Please activate the correct virtual environment before running this script.")

if __name__ == '__main__':
    # Determine the current operating system
    is_windows = platform.system() == 'Windows'

    # Use the correct script and shell depending on the operating system
    if is_windows:
        # Check if we are in Command Prompt or PowerShell
        comspec = os.getenv('ComSpec', '').lower()
        if 'powershell.exe' in comspec:
            script = 'shell-scripts\\setup_venv.ps1'
            shell = 'powershell'
            activate_command = '.\\venv\\Scripts\\activate'
        else:
            script = 'shell-scripts\\setup_venv.bat'
            shell = 'cmd'
            activate_command = 'venv\\Scripts\\activate.bat'
    else:
        script = 'shell-scripts/setup_venv.sh'
        shell = 'bash'
        activate_command = 'source venv/bin/activate'

    # Run the script
    subprocess.run([shell, script], check=True)

    # Print out the command to activate the virtual environment
    print(f"\nTo activate the virtual environment, run:\n\n{activate_command}\n")


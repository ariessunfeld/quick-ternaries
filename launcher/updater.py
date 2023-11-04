"""Updater script for quick-ternaries python package"""

import subprocess
import requests
from importlib.metadata import version, PackageNotFoundError

def get_latest_release(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/releases/latest"
    response = requests.get(url)
    tag_str = str(response.json()["tag_name"])
    return tag_str.lower().lstrip('v')

def get_installed_version(package_name):
    try:
        # Using importlib.metadata to get the current installed version
        return version(package_name).lower().lstrip('v')
    except PackageNotFoundError:
        # Return a default version if the package is not installed
        return '0.0.-1'

def update_to_latest(username, repo, package_name):
    latest_version = get_latest_release(username, repo)
    installed_version = get_installed_version(package_name)
    if installed_version < latest_version:
        if installed_version == '0.0.-1':
            installed_version = '[no installation found]'
        ans = input(f"\nVersion {latest_version} is available.\nYou have version {installed_version}.\nDo you want to update? [Y]/N: ")
        if ans.lower() in ['', 'y', 'yes']:
            cmd = f"pip install --upgrade git+https://github.com/{username}/{repo}.git@v{latest_version}"
            print('\nDownloading and installing... (this may take a minute)')
            subprocess.run(cmd, stdout=subprocess.DEVNULL, shell=True)

if __name__ == "__main__":

    USERNAME = 'ariessunfeld'
    REPO = 'quick-ternaries'
    PACKAGE_NAME = 'quick-ternaries'
    
    update_to_latest(USERNAME, REPO, PACKAGE_NAME)

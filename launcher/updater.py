"""Updater script for quick-ternaries python package"""

import os
import subprocess
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError

import requests


def get_latest_release(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/releases/latest"
    response = requests.get(url)
    tag_str = str(response.json()["tag_name"])
    return tag_str.lower().lstrip('v')


def get_installed_version(package_name):
    try:
        return version(package_name).lower().lstrip('v')
    except PackageNotFoundError:
        return '0.0.-1'


def update_to_latest(username, repo, package_name, log_file_path):
    python_invocation = 'python3' if os.name != 'nt' else 'python'

    latest_version = get_latest_release(username, repo)
    installed_version = get_installed_version(package_name)
    if installed_version < latest_version:
        if installed_version == '0.0.-1':
            installed_version = '[no installation found]'
        ans = input(
            f"\nVersion {latest_version} is available.\nYou have version {installed_version}.\nDo you want to update? [Y]/N: "
        )
        if ans.lower() in ['', 'y', 'yes']:
            cmd = f"{python_invocation} -m pip install --upgrade https://github.com/{username}/{repo}/archive/tags/v{latest_version}.tar.gz"
            with open(log_file_path, 'a') as log_file:
                log_file.write(f"{datetime.now()}: Executing command: {cmd}\n")
                print('\nDownloading and installing... (this may take a minute)')
                subprocess.run(cmd, stdout=log_file, stderr=log_file, shell=True)


if __name__ == "__main__":
    USERNAME = 'ariessunfeld'
    REPO = 'quick-ternaries'
    PACKAGE_NAME = 'quick-ternaries'
    LOG_FILE_PATH = 'update_log.txt'
    
    update_to_latest(USERNAME, REPO, PACKAGE_NAME, LOG_FILE_PATH)

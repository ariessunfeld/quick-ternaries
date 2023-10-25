"""Updater script for quick-ternaries python package"""

import requests
import subprocess
import pkg_resources

def get_latest_release(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/releases/latest"
    response = requests.get(url)
    tag_str = str(response.json()["tag_name"])
    return tag_str.lower().lstrip('v')

def get_installed_version(package_name):
    version = str(pkg_resources.get_distribution(package_name).version)
    return version.lower().lstrip('v')

def update_to_latest(username, repo, package_name):
    latest_version = get_latest_release(username, repo)
    installed_version = get_installed_version(package_name)
    if installed_version < latest_version:
        ans = input(f"Version {latest_version} is availabe. You have version {installed_version}. Do you want to update? [Y]/N: ")
        if ans.lower() in ['', 'y', 'yes']:
            cmd = f"pip install --upgrade git+https://github.com/{username}/{repo}.git@{latest_version}"
            subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    update_to_latest('ariessunfeld', 'quick-ternaries', 'quick-ternaries')

"""Updater script for quick-ternaries python package"""

import sys
import socket
import subprocess
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError

import requests


def can_connect_to_proxy(proxy_url, timeout=3):
    try:
        host, port = proxy_url.split("://")[1].split(":")
        port = int(port)

        # try to connect to the proxy server
        sock = socket.create_connection((host, port), timeout)
        sock.close()
        return True
    except Exception as e:
        #print(f"Proxy connection check failed: {e}")
        return False
    
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

def update_to_latest(username, repo, package_name, log_file_path):
    
    lanl_proxy_url = 'http://proxyout.lanl.gov:8080'

    latest_version = get_latest_release(username, repo)
    installed_version = get_installed_version(package_name)
    if installed_version < latest_version:
        if installed_version == '0.0.-1':
            installed_version = '[no installation found]'
        ans = input(f"\nVersion {latest_version} is available.\nYou have version {installed_version}.\nDo you want to update? [Y]/N: ")
        if ans.lower() in ['', 'y', 'yes']:

            if can_connect_to_proxy(lanl_proxy_url):
                cmd = f"python3 -m pip install --proxy={lanl_proxy_url} --upgrade https://github.com/{username}/{repo}/archive/tags/v{latest_version}.tar.gz"
            else:
                cmd = f"python3 -m pip install --upgrade https://github.com/{username}/{repo}/archive/tags/v{latest_version}.tar.gz"
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

"""Validate the exact GitHub release distributions before publishing to PyPI."""

import argparse
import configparser
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile


def release_version(tag):
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected an exact vX.Y.Z release tag")
    return tag[1:]


def check_distributions(tag, directory, release):
    version = release_version(tag)
    if release['tag_name'] != tag or release['draft'] or release['prerelease']:
        raise ValueError("Only the requested published stable release can be uploaded")
    expected = {
        f'quick_ternaries-{version}-py3-none-any.whl',
        f'quick_ternaries-{version}.tar.gz',
    }
    if {p.name for p in directory.iterdir()} != expected:
        raise ValueError("Publish exactly one package wheel and sdist; no other files")
    assets = {asset['name']: asset for asset in release['assets']}
    for name in sorted(expected):
        path = directory / name
        digest = 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()
        if assets.get(name, {}).get('digest') != digest:
            raise ValueError(f"GitHub release digest mismatch: {name}")
        if name.endswith('.whl'):
            with zipfile.ZipFile(path) as archive:
                metadata = archive.read(f'quick_ternaries-{version}.dist-info/METADATA')
        else:
            with tarfile.open(path) as archive:
                metadata = archive.extractfile(f'quick_ternaries-{version}/PKG-INFO').read()
        parsed = BytesParser().parsebytes(metadata)
        if parsed['Name'] != 'quick-ternaries' or parsed['Version'] != version:
            raise ValueError(f"Package metadata does not match {tag}: {name}")
        print(f'{digest}  {name}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag')
    parser.add_argument('directory', type=Path)
    parser.add_argument('release_json', type=Path)
    args = parser.parse_args()
    version = release_version(args.tag)
    ref = f'refs/tags/{args.tag}'
    subprocess.run(['git', 'merge-base', '--is-ancestor', ref, 'origin/main'], check=True)
    config = configparser.ConfigParser()
    config.read_string(subprocess.check_output(['git', 'show', f'{ref}:setup.cfg'], text=True))
    if config['metadata']['version'] != version:
        raise ValueError('Tag and setup.cfg version differ')
    check_distributions(args.tag, args.directory, json.loads(args.release_json.read_text()))


if __name__ == '__main__':
    main()

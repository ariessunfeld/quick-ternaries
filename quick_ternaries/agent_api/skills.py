"""Portable skill distribution; only the Python standard library is required."""

from hashlib import sha256
from importlib import resources
from io import BytesIO
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from tempfile import mkdtemp
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

NAME = 'quick-ternaries'
MANIFEST = '.quick-ternaries-skill.json'
# v1.4.0 installed these two files without a manifest. Recognize only that exact
# official bundle, never infer ownership from a filename or frontmatter alone.
LEGACY_FILES = {
    'SKILL.md': 'dfc2369340c08c6f7a1826424f7af3c5c7c04b66ba822235cec90006df560c1a',
    'references/connection.md': '14d479ced14d1931adab6bb10cecb062b585e788139cf1c1e0a6496a719d060b',
}


def bundled_files():
    root = resources.files('quick_ternaries').joinpath('resources', NAME)
    files = {}

    def visit(directory, prefix=''):
        for item in sorted(directory.iterdir(), key=lambda entry: entry.name):
            name = prefix + item.name
            if item.is_dir():
                visit(item, name + '/')
            else:
                files[name] = item.read_bytes()

    visit(root)
    return files


def _hashes(files):
    return {name: sha256(data).hexdigest() for name, data in files.items()}


def _manifest(files):
    return (json.dumps({'format': 1, 'name': NAME, 'files': _hashes(files)},
                       indent=2, sort_keys=True) + '\n').encode('utf-8')


def skill_destination(destination):
    hosts = {'codex': Path.home() / '.agents/skills' / NAME,
             'claude': Path.home() / '.claude/skills' / NAME}
    path = hosts.get(str(destination), Path(destination).expanduser()).absolute()
    if path.name != NAME:
        raise ValueError(f'The skill directory must be named {NAME}: {path}')
    return path


def _owned_files(destination, files):
    manifest = destination / MANIFEST
    if not manifest.exists():
        # Also adopt an exact unpacked current bundle. Never claim a partial one.
        for candidate in (_hashes(files), LEGACY_FILES):
            contents = {name: (destination / name).read_bytes() for name in candidate
                        if (destination / name).is_file()}
            actual = _hashes(contents)
            # A Windows checkout of the original release may have CRLF text.
            legacy_text = {name: data.replace(b'\r\n', b'\n') for name, data in contents.items()}
            if actual == candidate or (candidate == LEGACY_FILES and _hashes(legacy_text) == candidate):
                return actual
        raise ValueError('Existing skill is unmanaged or customized. Move it outside the host\'s '
                         'skills folder for review, then install a fresh copy.')
    try:
        value = json.loads(manifest.read_bytes())
        hashes = value['files']
        if value['format'] != 1 or value['name'] != NAME or not isinstance(hashes, dict) or 'SKILL.md' not in hashes:
            raise ValueError()
        for name, digest in hashes.items():
            path = PurePosixPath(name)
            if (not name or path.is_absolute() or path.as_posix() != name or
                    any(part in ('.', '..') for part in path.parts) or
                    '\\' in name or ':' in name or name == MANIFEST or
                    not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest)):
                raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise ValueError(f'Invalid skill ownership manifest: {manifest}. Restore or move that copy before installing.') from None
    return hashes


def _check_existing(destination, files, update):
    if destination.is_symlink():
        raise ValueError('Skill destination is a symlink. Manage its source directly or choose a regular directory.')
    if not destination.exists():
        if update:
            raise ValueError('Skill is not installed here. Use --install-skill first.')
        return {}
    if not destination.is_dir():
        raise ValueError(f'Skill destination is not a directory: {destination}')
    for item in destination.rglob('*'):
        if item.is_symlink() or not (item.is_file() or item.is_dir()):
            raise ValueError(f'Skill contains a symlink or special file; manage that copy manually: {item}')
    if not any(destination.iterdir()):
        if update:
            raise ValueError('Skill directory is empty. Use --install-skill first.')
        return {}
    owned = _owned_files(destination, files)
    for name, digest in owned.items():
        path = destination / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Customized or missing skill file: {path}. Move that copy outside the host\'s skills '
                             'folder for review before installing a fresh copy.')
    for name, data in files.items():
        path = destination / name
        if name not in owned and path.exists():
            raise ValueError(f'New bundled file conflicts with a local addition: {path}')
        if not update and (name not in owned or owned[name] != sha256(data).hexdigest()):
            raise ValueError('A different official skill is installed. Use --update-skill to update it.')
    if not update and owned.keys() != files.keys():
        raise ValueError('A different official skill is installed. Use --update-skill to update it.')
    return owned


def install_skill(destination, *, update=False):
    """Stage a whole bundle, preserve local additions, and roll back failed swaps.

    A sibling lock serializes installers. Hashes detect local edits; they are
    ownership bookkeeping, not a signature or a trust boundary against malware.
    """
    destination = skill_destination(destination)
    files = bundled_files()
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock = destination.parent / f'.{NAME}.install-lock'
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError(f'Skill installer lock exists: {lock}. Wait for the other installer; '
                         'after an interrupted install, review any staging backup before removing the lock.') from None
    try:
        owned = _check_existing(destination, files, update)
        def local_hashes():
            return {p.relative_to(destination).as_posix(): sha256(p.read_bytes()).hexdigest()
                    for p in destination.rglob('*') if p.is_file()}
        before = local_hashes()
        # Both renames stay on the destination filesystem, including on Windows.
        temporary = Path(mkdtemp(prefix=f'.{NAME}.staging-', dir=destination.parent))
        stage, backup = temporary / 'new', temporary / 'previous'
        installed = False
        try:
            if destination.exists():
                shutil.copytree(destination, stage)
            else:
                stage.mkdir()
            for name in owned.keys() - files.keys():
                (stage / name).unlink()
            for name, contents in {**files, MANIFEST: _manifest(files)}.items():
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(contents)
            # Detect edits/additions made while staging, before replacing the original.
            if _check_existing(destination, files, update) != owned or local_hashes() != before:
                raise ValueError('Skill changed during installation. Retry after local edits finish.')
            if destination.exists():
                destination.rename(backup)
            try:
                stage.rename(destination)
                installed = True
            except OSError:
                if backup.exists():
                    try:
                        backup.rename(destination)
                    except OSError:
                        raise OSError(f'Could not restore skill; recover the intact backup at {backup}') from None
                raise
        finally:
            # A failed rollback must never delete the only remaining original.
            if installed or not backup.exists():
                shutil.rmtree(temporary)
    finally:
        lock.rmdir()
    return destination


def export_skill(destination):
    """Export a reproducible, host-neutral archive from the installed package."""
    files = bundled_files()
    buffer = BytesIO()
    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
        for name, contents in sorted({**files, MANIFEST: _manifest(files)}.items()):
            info = ZipInfo(f'{NAME}/{name}', date_time=(2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, contents)
    destination = Path(destination).expanduser()
    data = buffer.getvalue()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        with destination.open('xb') as output:
            output.write(data)
    except FileExistsError:
        if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != data:
            raise ValueError(f'Existing archive differs: {destination}. Choose a new output path.') from None
    return destination

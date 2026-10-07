"""Distribution and update contracts for the portable, instruction-only skill."""
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from zipfile import ZipFile

import pytest

from quick_ternaries.agent_api import skills


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def older_bundle(monkeypatch, destination):
    current = skills.bundled_files()
    old = {**current, 'SKILL.md': current['SKILL.md'] + b'\nOld official instructions.\n',
           'references/retired.md': b'Former reference.\n'}
    with monkeypatch.context() as context:
        context.setattr(skills, 'bundled_files', lambda: old)
        skills.install_skill(destination)
    return current


def test_bundle_is_canonical_and_all_relative_references_ship():
    files = skills.bundled_files()
    entry = files['SKILL.md'].decode()
    assert entry.splitlines()[1] == f'name: {skills.NAME}'
    assert len(entry.splitlines()) < 100
    for name, data in files.items():
        if not name.endswith('.md'):
            continue
        for link in re.findall(r'\]\(([^)]+)\)', data.decode()):
            if '://' not in link and not link.startswith('#'):
                target = (Path(name).parent / link.split('#')[0]).as_posix()
                assert target in files, (name, link)
    assert {'references/connection.md', 'references/session.md'} <= files.keys()


def test_install_is_repeatable_and_records_content_not_machine_paths(tmp_path):
    target = tmp_path / skills.NAME
    assert skills.install_skill(target) == target
    first = snapshot(target)
    assert skills.install_skill(target) == target
    assert snapshot(target) == first
    manifest = json.loads(first[skills.MANIFEST])
    assert manifest['files'] == {k: sha256(v).hexdigest() for k, v in skills.bundled_files().items()}
    assert str(tmp_path) not in first[skills.MANIFEST].decode()


def test_explicit_update_preserves_additions_and_removes_retired_owned_files(tmp_path, monkeypatch):
    target = tmp_path / skills.NAME
    current = older_bundle(monkeypatch, target)
    (target / 'my-notes.txt').write_text('My local notes')
    before = snapshot(target)
    with pytest.raises(ValueError, match='--update-skill'):
        skills.install_skill(target)
    assert snapshot(target) == before
    skills.install_skill(target, update=True)
    assert not (target / 'references/retired.md').exists()
    assert (target / 'my-notes.txt').read_text() == 'My local notes'
    for name, data in current.items():
        assert (target / name).read_bytes() == data
    skills.install_skill(target, update=True)


@pytest.mark.parametrize('change', ['customize', 'delete', 'collision'])
def test_update_refuses_customizations_before_writing_any_file(tmp_path, monkeypatch, change):
    target = tmp_path / skills.NAME
    older_bundle(monkeypatch, target)
    if change == 'customize':
        (target / 'references/connection.md').write_text('My instructions')
    elif change == 'delete':
        (target / 'references/connection.md').unlink()
    else:
        current = skills.bundled_files()
        (target / 'references/new.md').write_text('My addition')
        monkeypatch.setattr(skills, 'bundled_files', lambda: {**current, 'references/new.md': b'Official addition'})
    before = snapshot(target)
    with pytest.raises(ValueError, match='Customized|conflicts'):
        skills.install_skill(target, update=True)
    assert snapshot(target) == before
    assert list(tmp_path.iterdir()) == [target]


@pytest.mark.parametrize('newline', [b'\n', b'\r\n'])
def test_previous_release_without_manifest_migrates_only_if_unmodified(tmp_path, newline):
    fixture = Path(__file__).parent / 'fixtures/skill-v1.4.0/quick-ternaries'
    assert {k: sha256(v).hexdigest() for k, v in snapshot(fixture).items()} == skills.LEGACY_FILES
    target = tmp_path / skills.NAME
    shutil.copytree(fixture, target)
    for path in target.rglob('*.md'):
        path.write_bytes(path.read_bytes().replace(b'\n', newline))
    skills.install_skill(target, update=True)
    assert (target / skills.MANIFEST).exists()
    shutil.rmtree(target)
    shutil.copytree(fixture, target)
    (target / 'SKILL.md').write_text('Customized legacy instructions')
    before = snapshot(target)
    with pytest.raises(ValueError, match='unmanaged or customized'):
        skills.install_skill(target, update=True)
    assert snapshot(target) == before


@pytest.mark.parametrize('bad', ['../escape', '/absolute', 'C:/escape', 'references\\escape', 'a//b', skills.MANIFEST])
def test_manifest_paths_cannot_escape_or_replace_bookkeeping(tmp_path, bad):
    target = skills.install_skill(tmp_path / skills.NAME)
    manifest = json.loads((target / skills.MANIFEST).read_bytes())
    manifest['files'][bad] = '0' * 64
    (target / skills.MANIFEST).write_text(json.dumps(manifest))
    before = snapshot(target)
    with pytest.raises(ValueError, match='Invalid skill ownership manifest'):
        skills.install_skill(target, update=True)
    assert snapshot(target) == before


def test_update_rolls_back_a_failed_directory_swap(tmp_path, monkeypatch):
    target = tmp_path / skills.NAME
    older_bundle(monkeypatch, target)
    before = snapshot(target)
    rename = Path.rename

    def fail_new(path, destination):
        if path.name == 'new':
            raise OSError('simulated replacement failure')
        return rename(path, destination)

    monkeypatch.setattr(Path, 'rename', fail_new)
    with pytest.raises(OSError, match='simulated'):
        skills.install_skill(target, update=True)
    assert snapshot(target) == before
    assert list(tmp_path.iterdir()) == [target]


def test_failed_rollback_retains_original_for_manual_recovery(tmp_path, monkeypatch):
    target = tmp_path / skills.NAME
    older_bundle(monkeypatch, target)
    before = snapshot(target)
    rename = Path.rename

    def fail_swap_and_restore(path, destination):
        if path.name in ('new', 'previous'):
            raise OSError('simulated filesystem failure')
        return rename(path, destination)

    monkeypatch.setattr(Path, 'rename', fail_swap_and_restore)
    with pytest.raises(OSError, match='recover the intact backup'):
        skills.install_skill(target, update=True)
    backup, = tmp_path.glob('.quick-ternaries.staging-*/previous')
    assert snapshot(backup) == before


def test_lock_prevents_overlapping_installers(tmp_path):
    lock = tmp_path / '.quick-ternaries.install-lock'
    lock.mkdir()
    with pytest.raises(ValueError, match='installer lock exists'):
        skills.install_skill(tmp_path / skills.NAME)
    assert list(tmp_path.iterdir()) == [lock]


def test_symlink_install_does_not_modify_its_source(tmp_path):
    source = skills.install_skill(tmp_path / 'source' / skills.NAME)
    target = tmp_path / skills.NAME
    before = snapshot(source)
    try:
        target.symlink_to(source, target_is_directory=True)
    except OSError:
        pytest.skip('OS does not permit symlink creation for this user')
    with pytest.raises(ValueError, match='symlink'):
        skills.install_skill(target, update=True)
    assert snapshot(source) == before


def test_host_paths_and_directory_name(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    assert skills.install_skill('codex') == tmp_path / '.agents/skills/quick-ternaries'
    assert skills.install_skill('claude') == tmp_path / '.claude/skills/quick-ternaries'
    with pytest.raises(ValueError, match='must be named'):
        skills.install_skill(tmp_path / 'wrong-name')
    with pytest.raises(ValueError, match='not installed'):
        skills.install_skill(tmp_path / skills.NAME, update=True)


def test_archive_is_reproducible_complete_and_installable(tmp_path):
    first = skills.export_skill(tmp_path / 'first.zip')
    second = skills.export_skill(tmp_path / 'second.zip')
    assert first.read_bytes() == second.read_bytes()
    assert skills.export_skill(first) == first
    with ZipFile(first) as archive:
        assert set(archive.namelist()) == {f'{skills.NAME}/{name}' for name in (*skills.bundled_files(), skills.MANIFEST)}
        archive.extractall(tmp_path / 'host-skills')
    target = tmp_path / 'host-skills' / skills.NAME
    skills.install_skill(target, update=True)
    second.write_bytes(b'user-owned archive')
    with pytest.raises(ValueError, match='Existing archive differs'):
        skills.export_skill(second)
    assert second.read_bytes() == b'user-owned archive'


def test_packaged_cli_works_outside_checkout_without_host_configuration(tmp_path):
    # -I and a different cwd prevent the checkout from shadowing the installed
    # wheel in CI. An editable developer install remains supported locally.
    target = tmp_path / skills.NAME
    before = os.environ.copy()
    for option, destination in [('--install-skill', target), ('--update-skill', target),
                                ('--export-skill', tmp_path / 'skill.zip')]:
        result = subprocess.run([sys.executable, '-I', '-m', 'quick_ternaries.agent_api.mcp',
                                 option, str(destination)], cwd=tmp_path, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        assert destination.exists()
    assert os.environ == before


def test_local_addition_edited_during_staging_is_preserved(tmp_path, monkeypatch):
    target = tmp_path / skills.NAME
    older_bundle(monkeypatch, target)
    local = target / 'notes.txt'
    local.write_text('Original')
    copytree = shutil.copytree

    def edit_while_staging(source, destination, *args, **kwargs):
        result = copytree(source, destination, *args, **kwargs)
        if source == target:
            local.write_text('New local edit')
        return result

    monkeypatch.setattr(shutil, 'copytree', edit_while_staging)
    with pytest.raises(ValueError, match='changed during installation'):
        skills.install_skill(target, update=True)
    assert local.read_text() == 'New local edit'
    assert b'Old official instructions.' in (target / 'SKILL.md').read_bytes()

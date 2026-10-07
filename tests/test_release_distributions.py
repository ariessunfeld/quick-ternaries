"""Reject wrong or tampered packages before handing them to the publisher."""
from email.message import EmailMessage
import hashlib
import io
import tarfile
import zipfile

import pytest

from scripts.check_release_distributions import check_distributions, release_version


@pytest.fixture
def release_files(tmp_path):
    metadata = EmailMessage()
    metadata['Name'] = 'quick-ternaries'
    metadata['Version'] = '1.5.0'
    payload = metadata.as_bytes()
    wheel = tmp_path / 'quick_ternaries-1.5.0-py3-none-any.whl'
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr('quick_ternaries-1.5.0.dist-info/METADATA', payload)
    source = tmp_path / 'quick_ternaries-1.5.0.tar.gz'
    with tarfile.open(source, 'w:gz') as archive:
        entry = tarfile.TarInfo('quick_ternaries-1.5.0/PKG-INFO')
        entry.size = len(payload)
        archive.addfile(entry, io.BytesIO(payload))
    release = dict(tag_name='v1.5.0', draft=False, prerelease=False, assets=[
        dict(name=p.name, digest='sha256:' + hashlib.sha256(p.read_bytes()).hexdigest())
        for p in (wheel, source)
    ])
    return tmp_path, release


def test_valid_release(release_files):
    directory, release = release_files
    check_distributions('v1.5.0', directory, release)


@pytest.mark.parametrize('tag', ['1.5.0', 'v1.5.0 — Editing', 'v1.5.0rc1', 'main', '../v1.5.0', 'v1.5.0\n'])
def test_invalid_tag(tag):
    with pytest.raises(ValueError):
        release_version(tag)


@pytest.mark.parametrize('field,value', [('draft', True), ('prerelease', True), ('tag_name', 'v1.4.0')])
def test_unpublished_or_wrong_release(release_files, field, value):
    directory, release = release_files
    release[field] = value
    with pytest.raises(ValueError, match='published stable'):
        check_distributions('v1.5.0', directory, release)


def test_tampered_asset(release_files):
    directory, release = release_files
    next(directory.glob('*.whl')).write_bytes(b'changed after release')
    with pytest.raises(ValueError, match='digest mismatch'):
        check_distributions('v1.5.0', directory, release)


def test_skill_zip_cannot_be_uploaded(release_files):
    directory, release = release_files
    (directory / 'quick-ternaries-skill-1.5.0.zip').write_bytes(b'skill')
    with pytest.raises(ValueError, match='exactly one'):
        check_distributions('v1.5.0', directory, release)


def test_wrong_package_identity_even_with_matching_digest(release_files):
    directory, release = release_files
    wheel = next(directory.glob('*.whl'))
    with zipfile.ZipFile(wheel, 'w') as archive:
        archive.writestr('quick_ternaries-1.5.0.dist-info/METADATA', 'Name: another-package\nVersion: 1.5.0\n')
    release['assets'][0]['digest'] = 'sha256:' + hashlib.sha256(wheel.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match='metadata'):
        check_distributions('v1.5.0', directory, release)

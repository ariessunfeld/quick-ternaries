"""Run previous-release updaters against a candidate wheel, without live GitHub.

Only release metadata and the artifact URL are substituted. The previous code
selects the version/command, and pip really replaces its installed package.
Run from a development environment with build, requests, and candidate runtime
dependencies installed. Each method gets a disposable, isolated package install.
"""

import argparse
from contextlib import ExitStack
from email.parser import BytesParser
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import venv
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("cli", "launcher", "conda-launcher")
REAL_RUN = subprocess.run


def wheel_version(wheel):
    with ZipFile(wheel) as archive:
        names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(names) != 1:
            raise ValueError("Expected one package metadata entry")
        metadata = BytesParser().parsebytes(archive.read(names[0]))
        if metadata["Name"].replace("_", "-") != "quick-ternaries":
            raise ValueError("Candidate is not Quick Ternaries")
        return metadata["Version"]


def run(command, **kwargs):
    return REAL_RUN([str(part) for part in command], check=True, **kwargs)


def probe(method, previous_source, candidate, previous_version):
    from importlib.metadata import version

    assert version("quick-ternaries") == previous_version, "Previous package is not installed"
    candidate_version = wheel_version(candidate)
    tag = f"v{candidate_version}"
    expected_url = f"https://github.com/ariessunfeld/quick-ternaries/archive/tags/{tag}.tar.gz"
    payload = {"tag_name": tag, "name": f"{tag} — Descriptive title 🚀",
               "body": "Release notes deliberately are not a version."}
    commands = []

    def install(command, **kwargs):
        commands.append(command)
        if isinstance(command, list):
            assert command == [sys.executable, "-m", "pip", "install", "--upgrade", expected_url]
            return REAL_RUN(command[:-1] + ["--no-deps", str(candidate)], **kwargs)
        interpreter = "python" if os.name == "nt" else "python3"
        assert command == f"{interpreter} -m pip install --upgrade {expected_url}"
        # Exercise the actual activated-environment shell path used by launchers.
        quoted = subprocess.list2cmdline([str(candidate)]) if os.name == "nt" else shlex.quote(str(candidate))
        return REAL_RUN(command.replace(expected_url, "--no-deps " + quoted), **kwargs)

    if method == "cli":
        from quick_ternaries import main as entry, updater

        class Response(io.BytesIO):
            pass

        def opener(request, timeout):
            assert request.full_url == updater.LATEST_RELEASE_API
            return Response(json.dumps(payload).encode())

        update = updater.run_update_command
        with patch.object(updater, "run_update_command", lambda: update(opener=opener, runner=install)):
            assert entry.main(["--update"]) == 0
    else:
        relative = ("launcher/updater.py" if method == "launcher" else
                    "launcher/quick-ternaries-mac-conda-launcher/updater.py")
        spec = importlib.util.spec_from_file_location("previous_launcher", previous_source / relative)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def release_response(url):
            assert url == "https://api.github.com/repos/ariessunfeld/quick-ternaries/releases/latest"
            return SimpleNamespace(json=lambda: payload)

        with ExitStack() as stack:
            stack.enter_context(patch.object(module.requests, "get", release_response))
            stack.enter_context(patch("builtins.input", return_value="y"))
            stack.enter_context(patch.object(module.subprocess, "run", install))
            if hasattr(module, "can_connect_to_proxy"):
                # Proxy command construction is covered by contract tests. Do not
                # contact an institution's proxy in a portable installer check.
                stack.enter_context(patch.object(module, "can_connect_to_proxy", return_value=False))
            module.update_to_latest("ariessunfeld", "quick-ternaries", "quick-ternaries", "upgrade.log")
    assert len(commands) == 1, "The old updater did not attempt exactly one install"
    assert version("quick-ternaries") == candidate_version, "Upgrade did not install the candidate"
    entry_point = Path(sys.executable).parent / ("quick-ternaries.exe" if os.name == "nt" else "quick-ternaries")
    run([entry_point, "--help"])
    print(f"UPGRADE_OK {method}: {previous_version} -> {candidate_version}", flush=True)


def check_upgrade(from_ref, wheel_dir):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", from_ref):
        raise ValueError("Use an exact previous package tag, vX.Y.Z")
    wheels = list(wheel_dir.resolve().glob("quick_ternaries-*.whl"))
    if len(wheels) != 1:
        raise ValueError("Use a directory containing exactly one candidate wheel")
    candidate = wheels[0]
    candidate_version = wheel_version(candidate)
    if tuple(map(int, candidate_version.split("."))) <= tuple(map(int, from_ref[1:].split("."))):
        raise ValueError("Candidate must be newer than the previous release")
    with tempfile.TemporaryDirectory(prefix="quick-ternaries-upgrade-") as directory:
        temp = Path(directory)
        previous_source = temp / "previous"
        previous_source.mkdir()
        archive = REAL_RUN(["git", "archive", "--format=tar", from_ref], cwd=ROOT,
                           capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(previous_source, filter="data")
        previous_dist = temp / "previous-dist"
        run([sys.executable, "-m", "build", "--wheel", "--outdir", previous_dist, previous_source])
        previous_wheel = next(previous_dist.glob("*.whl"))
        for method in METHODS:
            environment = temp / method
            venv.EnvBuilder(with_pip=True, system_site_packages=True).create(environment)
            scripts = environment / ("Scripts" if os.name == "nt" else "bin")
            python = scripts / ("python.exe" if os.name == "nt" else "python")
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            env.update(PATH=str(scripts) + os.pathsep + env.get("PATH", ""),
                       PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_INDEX="1")
            run([python, "-m", "pip", "install", "--ignore-installed", "--no-deps", previous_wheel],
                cwd=temp, env=env)
            run([python, Path(__file__).resolve(), "--probe", method, "--previous-source", previous_source,
                 "--candidate", candidate, "--previous-version", from_ref[1:]], cwd=temp, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-ref")
    parser.add_argument("--wheel-dir", type=Path)
    parser.add_argument("--probe", choices=METHODS, help=argparse.SUPPRESS)
    parser.add_argument("--previous-source", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--candidate", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--previous-version", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.probe:
        probe(args.probe, args.previous_source, args.candidate, args.previous_version)
    else:
        if not args.from_ref or not args.wheel_dir:
            parser.error("--from-ref and --wheel-dir are required")
        check_upgrade(args.from_ref, args.wheel_dir)


if __name__ == "__main__":
    main()

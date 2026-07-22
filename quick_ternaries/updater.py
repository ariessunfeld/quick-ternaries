import json
import re
import subprocess
import sys
from dataclasses import dataclass
from importlib import metadata
from json import JSONDecodeError
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


GITHUB_OWNER = "ariessunfeld"
GITHUB_REPO = "quick-ternaries"
PACKAGE_NAME = "quick-ternaries"
LATEST_RELEASE_API = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
DEFAULT_TIMEOUT_SECONDS = 15
_VERSION_RE = re.compile(r"^v?(?P<version>\d+(?:\.\d+){1,3})(?:[-+].*)?$")


class UpdateError(RuntimeError):
    """Raised when the update check cannot determine or install a release."""


@dataclass(frozen=True)
class LatestRelease:
    tag_name: str
    version: str
    html_url: str
    install_url: str


def normalize_version(value: str) -> str:
    match = _VERSION_RE.match(value.strip())
    if not match:
        raise UpdateError(f"Unsupported version format: {value!r}")
    return match.group("version")


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in normalize_version(value).split("."))


def is_newer_version(candidate: str, current: str) -> bool:
    candidate_parts = version_tuple(candidate)
    current_parts = version_tuple(current)
    width = max(len(candidate_parts), len(current_parts))
    return candidate_parts + (0,) * (width - len(candidate_parts)) > current_parts + (
        0,
    ) * (width - len(current_parts))


def release_install_url(tag_name: str) -> str:
    quoted_tag = quote(tag_name, safe="")
    return (
        f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/archive/tags/"
        f"{quoted_tag}.tar.gz"
    )


def fetch_latest_release(
    *,
    opener: Callable = urlopen,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> LatestRelease:
    request = Request(
        LATEST_RELEASE_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{PACKAGE_NAME}-updater",
        },
    )

    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise UpdateError(
            f"GitHub release check failed with HTTP {exc.code}: {exc.reason}"
        ) from exc
    except URLError as exc:
        raise UpdateError(f"Could not reach GitHub releases: {exc.reason}") from exc
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        raise UpdateError("GitHub release response was not valid JSON.") from exc

    tag_name = payload.get("tag_name")
    html_url = payload.get("html_url", "")
    if not isinstance(tag_name, str) or not tag_name:
        raise UpdateError("GitHub release response did not include a tag name.")

    return LatestRelease(
        tag_name=tag_name,
        version=normalize_version(tag_name),
        html_url=html_url,
        install_url=release_install_url(tag_name),
    )


def installed_version() -> str:
    try:
        return metadata.version(PACKAGE_NAME)
    except metadata.PackageNotFoundError as exc:
        raise UpdateError(
            "Could not determine the installed Quick Ternaries version. "
            "Install the package with pip before using --update."
        ) from exc


def run_update_command(
    *,
    stdout=None,
    stderr=None,
    runner: Callable = subprocess.run,
    opener: Callable = urlopen,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> int:
    stdout = sys.stdout if stdout is None else stdout
    stderr = sys.stderr if stderr is None else stderr

    try:
        current_version = installed_version()
        latest_release = fetch_latest_release(opener=opener, timeout=timeout)
    except UpdateError as exc:
        print(f"Unable to update Quick Ternaries: {exc}", file=stderr)
        return 1

    if not is_newer_version(latest_release.version, current_version):
        print(
            "Quick Ternaries is already up to date "
            f"({current_version}; latest release is {latest_release.tag_name}).",
            file=stdout,
        )
        return 0

    print(
        "Updating Quick Ternaries "
        f"from {current_version} to {latest_release.version}...",
        file=stdout,
    )
    print(f"Installing from {latest_release.install_url}", file=stdout)

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--upgrade",
        latest_release.install_url,
    ]

    try:
        completed = runner(command)
    except OSError as exc:
        print(f"Unable to run pip: {exc}", file=stderr)
        return 1

    return_code = getattr(completed, "returncode", 0)
    if return_code != 0:
        print(
            "Quick Ternaries update failed. "
            "Review the pip output above and try again.",
            file=stderr,
        )
        return return_code

    print(
        "Update complete. Restart Quick Ternaries by running `quick-ternaries`.",
        file=stdout,
    )
    return 0

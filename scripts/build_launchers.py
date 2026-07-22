"""Build deterministic launcher ZIP files from tracked source files."""

from argparse import ArgumentParser
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_ROOT = PROJECT_ROOT / "launcher"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "dist" / "launchers"
ARCHIVE_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


ARCHIVES = {
    "quick-ternaries-mac-launcher.zip": (
        ("updater.py", "updater.py", False),
        ("requirements.txt", "requirements.txt", False),
        ("quick-ternaries_mac.command", "quick-ternaries_mac.command", True),
    ),
    "quick-ternaries-windows-launcher.zip": (
        ("updater.py", "updater.py", False),
        ("requirements.txt", "requirements.txt", False),
        ("quick-ternaries_windows.bat", "quick-ternaries_windows.bat", False),
    ),
    "quick-ternaries-mac-conda-launcher.zip": (
        (
            "quick-ternaries-mac-conda-launcher/environment.yml",
            "environment.yml",
            False,
        ),
        (
            "quick-ternaries-mac-conda-launcher/quick-ternaries_mac_conda.command",
            "quick-ternaries_mac_conda.command",
            True,
        ),
        (
            "quick-ternaries-mac-conda-launcher/updater.py",
            "updater.py",
            False,
        ),
    ),
    "QuickTernaries.zip": (
        (
            "windows-conda-launcher/setup.bat",
            "QuickTernaries/setup.bat",
            False,
        ),
        (
            "windows-conda-launcher/TemplateLauncher.bat",
            "QuickTernaries/TemplateLauncher.bat",
            False,
        ),
        ("environment.yml", "QuickTernaries/environment.yml", False),
        ("updater.py", "QuickTernaries/updater.py", False),
    ),
}


def _write_file(archive, source_path, archive_path, executable):
    info = ZipInfo(archive_path, date_time=ARCHIVE_TIMESTAMP)
    info.compress_type = ZIP_DEFLATED
    info.create_system = 3
    mode = 0o755 if executable else 0o644
    info.external_attr = mode << 16
    archive.writestr(info, source_path.read_bytes())


def build_launchers(output_dir=DEFAULT_OUTPUT_DIR):
    """Build every launcher archive and return their output paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []

    for archive_name, members in ARCHIVES.items():
        output_path = output_dir / archive_name
        with ZipFile(output_path, "w") as archive:
            for source_name, archive_path, executable in members:
                _write_file(
                    archive,
                    LAUNCHER_ROOT / source_name,
                    archive_path,
                    executable,
                )
        outputs.append(output_path)

    return outputs


def main(argv=None):
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated launcher ZIPs.",
    )
    args = parser.parse_args(argv)

    for output_path in build_launchers(args.output_dir):
        print(output_path)


if __name__ == "__main__":
    main()

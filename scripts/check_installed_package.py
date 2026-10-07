"""Smoke-test an installed release outside a checkout; never use source imports."""

import argparse
from importlib import metadata, resources
from pathlib import Path
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('--agent', action='store_true')
    args = parser.parse_args()
    import quick_ternaries

    assert metadata.version('quick-ternaries') == args.version
    package_path = Path(quick_ternaries.__file__).resolve()
    assert 'site-packages' in package_path.parts, package_path
    bundle = resources.files('quick_ternaries').joinpath('resources', 'quick-ternaries')
    for name in ('SKILL.md', 'references/connection.md', 'references/session.md'):
        assert bundle.joinpath(name).read_text(encoding='utf-8').strip(), name
    from quick_ternaries.agent_api.skills import export_skill
    with tempfile.TemporaryDirectory() as directory:
        export_skill(Path(directory) / 'quick-ternaries-skill.zip')
    if args.agent:
        from quick_ternaries.agent_api.mcp import create_server
        create_server()
        print('Installed MCP adapter and skill OK')
        return
    assert 'mcp' not in sys.modules
    from PySide6.QtWidgets import QApplication
    from quick_ternaries.app import MainWindow
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.processEvents()
    assert window.agent_dialog is None
    window.close()
    assert 'mcp' not in sys.modules
    print(f'Installed desktop {args.version} starts with agent access off')


if __name__ == '__main__':
    main()

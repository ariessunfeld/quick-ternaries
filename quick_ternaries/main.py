import sys
from argparse import ArgumentParser


def build_parser():
    parser = ArgumentParser(prog="quick-ternaries", allow_abbrev=False)
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update Quick Ternaries from the latest GitHub release and exit.",
    )
    return parser


def launch_app(argv):
    from PySide6.QtWidgets import QApplication

    from quick_ternaries.app import MainWindow

    app = QApplication(argv)
    window = MainWindow()
    window.show()
    return app.exec()


# --------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    args, app_args = parser.parse_known_args(argv)

    if args.update:
        if app_args:
            parser.error("--update cannot be combined with other arguments")
        from quick_ternaries.updater import run_update_command

        return run_update_command()

    return launch_app([sys.argv[0], *app_args])


if __name__ == "__main__":
    sys.exit(main())

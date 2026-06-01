from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = PACKAGE_ROOT / "resources" / "fonts"

OPEN_SANS_REGULAR_FONT = FONTS_DIR / "OpenSans-Regular.ttf"
OPEN_SANS_ITALIC_FONT = FONTS_DIR / "OpenSans-Italic.ttf"
OPEN_SANS_FONT_FILES = (
    OPEN_SANS_REGULAR_FONT,
    OPEN_SANS_ITALIC_FONT,
)

from pathlib import Path
from typing import Any

from quick_ternaries.utils.fonts import (
    OPEN_SANS_ITALIC_FONT,
    OPEN_SANS_REGULAR_FONT,
)


OPEN_SANS_STYLE_ID = "quick-ternaries-open-sans-fonts"


def _font_uri(font_path: Path) -> str:
    return font_path.resolve().as_uri()


def open_sans_font_face_style() -> str:
    """Build the font-face CSS that makes bundled Open Sans available to Plotly."""
    regular_uri = _font_uri(OPEN_SANS_REGULAR_FONT)
    italic_uri = _font_uri(OPEN_SANS_ITALIC_FONT)
    return f"""
<style id="{OPEN_SANS_STYLE_ID}">
@font-face {{
  font-family: "Open Sans";
  font-style: normal;
  font-weight: 300 800;
  font-stretch: 75% 100%;
  src: url("{regular_uri}") format("truetype");
}}
@font-face {{
  font-family: "Open Sans";
  font-style: italic;
  font-weight: 300 800;
  font-stretch: 75% 100%;
  src: url("{italic_uri}") format("truetype");
}}
</style>
""".strip()


def inject_open_sans_font_faces(html: str) -> str:
    """Inject bundled Open Sans support while preserving Plotly's default font."""
    if OPEN_SANS_STYLE_ID in html:
        return html

    style = open_sans_font_face_style()
    if "</head>" in html:
        return html.replace("</head>", f"{style}\n</head>", 1)
    return f"{style}\n{html}"


def figure_to_html(fig: Any, **kwargs: Any) -> str:
    """Render a Plotly figure to HTML with bundled Open Sans support."""
    return inject_open_sans_font_faces(fig.to_html(**kwargs))


def write_plotly_html(fig: Any, filepath: str | Path, **kwargs: Any) -> None:
    """Write Plotly HTML with bundled Open Sans support."""
    Path(filepath).write_text(figure_to_html(fig, **kwargs), encoding="utf-8")

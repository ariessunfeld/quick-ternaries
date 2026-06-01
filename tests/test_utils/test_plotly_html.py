import plotly.graph_objects as go

from quick_ternaries.utils.fonts import (
    OPEN_SANS_FONT_FILES,
    OPEN_SANS_ITALIC_FONT,
    OPEN_SANS_REGULAR_FONT,
)
from quick_ternaries.utils.plotly_html import (
    OPEN_SANS_STYLE_ID,
    figure_to_html,
    inject_open_sans_font_faces,
    open_sans_font_face_style,
    write_plotly_html,
)


def test_open_sans_font_assets_are_bundled():
    for font_path in OPEN_SANS_FONT_FILES:
        assert font_path.is_file()
        assert font_path.stat().st_size > 0


def test_open_sans_font_face_style_references_bundled_assets():
    style = open_sans_font_face_style()

    assert OPEN_SANS_STYLE_ID in style
    assert 'font-family: "Open Sans";' in style
    assert "font-style: normal;" in style
    assert "font-style: italic;" in style
    assert OPEN_SANS_REGULAR_FONT.resolve().as_uri() in style
    assert OPEN_SANS_ITALIC_FONT.resolve().as_uri() in style


def test_inject_open_sans_font_faces_adds_style_once():
    html = "<html><head></head><body></body></html>"

    injected = inject_open_sans_font_faces(html)
    injected_again = inject_open_sans_font_faces(injected)

    assert injected.count(OPEN_SANS_STYLE_ID) == 1
    assert injected_again.count(OPEN_SANS_STYLE_ID) == 1
    assert injected.index(OPEN_SANS_STYLE_ID) < injected.index("</head>")


def test_figure_to_html_preserves_plotly_open_sans_default():
    fig = go.Figure(data=go.Scatter(x=[1, 2], y=[3, 4]))

    html = figure_to_html(fig, include_plotlyjs=True, full_html=True)

    assert OPEN_SANS_STYLE_ID in html
    assert 'font-family: "Open Sans";' in html
    assert '"Open Sans"' in html


def test_write_plotly_html_writes_bundled_open_sans_support(tmp_path):
    fig = go.Figure(data=go.Scatter(x=[1, 2], y=[3, 4]))
    filepath = tmp_path / "plot.html"

    write_plotly_html(fig, filepath, include_plotlyjs=True, full_html=True)

    html = filepath.read_text(encoding="utf-8")
    assert OPEN_SANS_STYLE_ID in html
    assert OPEN_SANS_REGULAR_FONT.resolve().as_uri() in html

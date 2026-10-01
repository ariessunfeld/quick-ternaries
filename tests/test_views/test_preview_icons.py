"""Control previews must render without launching Plotly's image exporter."""

import pytest
import plotly.io as pio
from plotly.colors import get_colorscale, unlabel_rgb
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from quick_ternaries.views.widgets.color_scale_dropdown import ColorScaleDropdown
from quick_ternaries.views.widgets.shape_button_with_menu_widget import ShapeButtonWithMenu


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def forbid_image_export(monkeypatch):
    calls = []

    def unexpected_export(*args, **kwargs):
        calls.append(True)
        raise AssertionError("Widget previews must not export Plotly images")

    monkeypatch.setattr(pio, "to_image", unexpected_export)
    ColorScaleDropdown._icon_cache.clear()
    ShapeButtonWithMenu._icon_cache.clear()
    yield
    # A widget's error handler must not hide an attempted export.
    assert not calls


def rgb(color):
    if color.startswith("rgb("):
        return tuple(round(channel) for channel in unlabel_rgb(color))
    return QColor(color).getRgb()[:3]


def test_all_colorscale_previews_match_plotly_stops(qt_app):
    widget = ColorScaleDropdown()
    for name in widget.PLOTLY_COLOR_SCALES:
        image = widget.create_colorscale_icon(name, 151, 20).pixmap(151, 20).toImage()
        assert not image.isNull(), name
        for position, color in get_colorscale(name):
            actual = image.pixelColor(round(position * 150), 10).getRgb()
            # A stop may fall between pixels; allow interpolation/rounding error.
            assert actual[3] == 255, name
            assert all(abs(a - b) <= 5 for a, b in zip(actual[:3], rgb(color))), name
    widget.close()


def test_marker_previews_have_visible_shapes_and_transparent_background(qt_app):
    widget = ShapeButtonWithMenu()
    for name in widget.PLOTLY_SHAPES:
        for size in (16, 24, 32, 64):
            image = widget.create_plotly_marker_icon(name).pixmap(size, size).toImage()
            assert not image.isNull(), name
            alphas = [image.pixelColor(x, y).alpha()
                      for x in range(image.width()) for y in range(image.height())]
            assert 0 in alphas, name
            assert 255 in alphas, name
            # Tips must fit inside the icon rather than being clipped at its edge.
            for edge in range(size):
                for x, y in ((edge, 0), (edge, size - 1), (0, edge), (size - 1, edge)):
                    assert image.pixelColor(x, y).alpha() == 0, name
    widget.close()


def test_preview_controls_keep_selection_signals_and_fallbacks(qt_app):
    colors = ColorScaleDropdown("Viridis")
    color_changes = []
    colors.colorScaleChanged.connect(color_changes.append)
    colors.comboBox.setCurrentText("Plasma")
    assert colors.getColorScale() == "Plasma"
    assert color_changes == ["Plasma"]
    assert not colors.create_colorscale_icon("unknown-scale").isNull()

    shapes = ShapeButtonWithMenu("circle")
    shape_changes = []
    shapes.shapeChanged.connect(shape_changes.append)
    next(action for action in shapes.menu.actions() if action.text() == "star").trigger()
    assert shapes.getShape() == "star"
    assert shape_changes == ["star"]
    shapes.setShape("unknown-shape")
    assert shapes.getShape() == "circle"
    assert not shapes.shapePreview.pixmap().isNull()
    colors.close()
    shapes.close()

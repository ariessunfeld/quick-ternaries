from types import SimpleNamespace

from quick_ternaries.utils.legend_layout import (
    build_legend_layout,
    normalize_legend_position,
)


def test_normalize_legend_position_accepts_legacy_freeform_values():
    assert normalize_legend_position("Top Right") == "top-right"
    assert normalize_legend_position("left bottom") == "bottom-left"
    assert normalize_legend_position("middle") == "center"


def test_build_legend_layout_uses_position_preset():
    settings = SimpleNamespace(
        legend_position="bottom-left",
        legend_orientation="horizontal",
    )
    legend = build_legend_layout(settings, {"family": "Arial", "size": 12})

    assert legend["x"] == 0.0
    assert legend["y"] == 0.0
    assert legend["xref"] == "paper"
    assert legend["yref"] == "paper"
    assert legend["xanchor"] == "left"
    assert legend["yanchor"] == "bottom"
    assert legend["orientation"] == "h"
    assert legend["font"] == {"family": "Arial", "size": 12}


def test_build_legend_layout_uses_custom_coordinates_and_anchors():
    settings = SimpleNamespace(
        legend_position="custom",
        legend_x=1.25,
        legend_y=-0.15,
        legend_coordinate_reference="paper",
        legend_xanchor="left",
        legend_yanchor="bottom",
        legend_orientation="vertical",
    )
    legend = build_legend_layout(settings)

    assert legend["x"] == 1.25
    assert legend["y"] == -0.15
    assert legend["xref"] == "paper"
    assert legend["yref"] == "paper"
    assert legend["xanchor"] == "left"
    assert legend["yanchor"] == "bottom"
    assert legend["orientation"] == "v"


def test_build_legend_layout_clamps_container_coordinates():
    settings = SimpleNamespace(
        legend_position="custom",
        legend_x=1.25,
        legend_y=-0.15,
        legend_coordinate_reference="container",
        legend_xanchor="left",
        legend_yanchor="bottom",
        legend_orientation="vertical",
    )
    legend = build_legend_layout(settings)

    assert legend["x"] == 1.0
    assert legend["y"] == 0.0
    assert legend["xref"] == "container"
    assert legend["yref"] == "container"

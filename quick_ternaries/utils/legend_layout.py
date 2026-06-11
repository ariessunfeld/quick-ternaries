"""Helpers for applying shared Plotly legend layout settings."""

from typing import Any, Dict


LEGEND_POSITION_PRESETS = {
    "top-left": {"x": 0.0, "y": 1.0, "xanchor": "left", "yanchor": "top"},
    "top-center": {"x": 0.5, "y": 1.0, "xanchor": "center", "yanchor": "top"},
    "top-right": {"x": 1.0, "y": 1.0, "xanchor": "right", "yanchor": "top"},
    "center-left": {"x": 0.0, "y": 0.5, "xanchor": "left", "yanchor": "middle"},
    "center": {"x": 0.5, "y": 0.5, "xanchor": "center", "yanchor": "middle"},
    "center-right": {"x": 1.0, "y": 0.5, "xanchor": "right", "yanchor": "middle"},
    "bottom-left": {"x": 0.0, "y": 0.0, "xanchor": "left", "yanchor": "bottom"},
    "bottom-center": {"x": 0.5, "y": 0.0, "xanchor": "center", "yanchor": "bottom"},
    "bottom-right": {"x": 1.0, "y": 0.0, "xanchor": "right", "yanchor": "bottom"},
}

LEGEND_POSITION_OPTIONS = [
    "top-right",
    "top-left",
    "bottom-right",
    "bottom-left",
    "top-center",
    "bottom-center",
    "center-right",
    "center-left",
    "center",
    "custom",
]

LEGEND_X_ANCHOR_OPTIONS = ["left", "center", "right"]
LEGEND_Y_ANCHOR_OPTIONS = ["top", "middle", "bottom"]
LEGEND_ORIENTATION_OPTIONS = ["vertical", "horizontal"]
LEGEND_COORDINATE_REFERENCE_OPTIONS = ["paper", "container"]

_POSITION_ALIASES = {
    "left-top": "top-left",
    "center-top": "top-center",
    "right-top": "top-right",
    "left-center": "center-left",
    "middle-left": "center-left",
    "left-middle": "center-left",
    "middle": "center",
    "right-center": "center-right",
    "middle-right": "center-right",
    "right-middle": "center-right",
    "left-bottom": "bottom-left",
    "center-bottom": "bottom-center",
    "right-bottom": "bottom-right",
}


def normalize_legend_position(position: Any) -> str:
    """Normalize saved/free-form legend position values to known options."""
    normalized = str(position or "top-right").strip().lower()
    normalized = normalized.replace("_", "-").replace(" ", "-")
    return _POSITION_ALIASES.get(normalized, normalized)


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_option(value: Any, allowed: list[str], default: str) -> str:
    normalized = str(value or default).strip().lower()
    return normalized if normalized in allowed else default


def _orientation_value(value: Any) -> str:
    normalized = str(value or "vertical").strip().lower()
    return "h" if normalized.startswith("h") else "v"


def _clamp_container_coordinate(value: float) -> float:
    return max(0.0, min(1.0, value))


def build_legend_layout(
    advanced_settings: Any,
    font_settings: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a Plotly layout.legend dict from global advanced settings."""
    position = normalize_legend_position(
        getattr(advanced_settings, "legend_position", "top-right")
    )
    preset = LEGEND_POSITION_PRESETS.get(position, LEGEND_POSITION_PRESETS["top-right"])
    coordinate_reference = "paper"

    if position == "custom":
        x = _coerce_float(getattr(advanced_settings, "legend_x", preset["x"]), preset["x"])
        y = _coerce_float(getattr(advanced_settings, "legend_y", preset["y"]), preset["y"])
        coordinate_reference = _coerce_option(
            getattr(advanced_settings, "legend_coordinate_reference", "paper"),
            LEGEND_COORDINATE_REFERENCE_OPTIONS,
            "paper",
        )
        if coordinate_reference == "container":
            x = _clamp_container_coordinate(x)
            y = _clamp_container_coordinate(y)
        xanchor = _coerce_option(
            getattr(advanced_settings, "legend_xanchor", preset["xanchor"]),
            LEGEND_X_ANCHOR_OPTIONS,
            preset["xanchor"],
        )
        yanchor = _coerce_option(
            getattr(advanced_settings, "legend_yanchor", preset["yanchor"]),
            LEGEND_Y_ANCHOR_OPTIONS,
            preset["yanchor"],
        )
    else:
        x = preset["x"]
        y = preset["y"]
        xanchor = preset["xanchor"]
        yanchor = preset["yanchor"]

    legend = {
        "x": x,
        "y": y,
        "xref": coordinate_reference,
        "yref": coordinate_reference,
        "xanchor": xanchor,
        "yanchor": yanchor,
        "orientation": _orientation_value(
            getattr(advanced_settings, "legend_orientation", "vertical")
        ),
        "bordercolor": "#888",
        "borderwidth": 1,
    }

    if font_settings:
        legend["font"] = font_settings

    return legend

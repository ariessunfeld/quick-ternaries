"""Regenerate the bundled marker previews with one Plotly SVG export.

Run from an installed development checkout. Kaleido and Chrome are needed only
to regenerate these assets, not to display the app's shape selector.
"""

from pathlib import Path
import sys
from xml.etree import ElementTree as ET

import plotly.graph_objects as go

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from quick_ternaries.views.widgets.shape_button_with_menu_widget import (
    MARKER_ICON_DIR,
    ShapeButtonWithMenu,
)


def build_marker_icons(output_dir=MARKER_ICON_DIR):
    shapes = ShapeButtonWithMenu.PLOTLY_SHAPES
    figure = go.Figure(go.Scatter(
        x=list(range(len(shapes))), y=[0] * len(shapes), mode="markers",
        marker=dict(symbol=shapes, size=25.6, color="black", line_width=0),
    ))
    figure.update_layout(
        width=len(shapes) * 40, height=40,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, range=[-0.5, len(shapes) - 0.5]),
        yaxis=dict(visible=False, range=[-1, 1]),
        showlegend=False,
    )
    svg = ET.fromstring(figure.to_image(format="svg"))
    paths = [node for node in svg.iter() if node.get("class") == "point"]
    if len(paths) != len(shapes):
        raise ValueError(f"Expected {len(shapes)} marker paths, got {len(paths)}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, path in zip(shapes, paths):
        icon = ET.Element("svg", {
            "xmlns": "http://www.w3.org/2000/svg", "width": "32", "height": "32",
            # Stars and diamonds extend beyond half the nominal marker size.
            # Leave enough room for their tips at every rendered icon size.
            "viewBox": "-24 -24 48 48",
        })
        ET.SubElement(icon, "path", {"d": path.attrib["d"], "fill": "black"})
        (output_dir / f"{name}.svg").write_text(
            ET.tostring(icon, encoding="unicode") + "\n", encoding="utf-8"
        )
    return len(paths)


if __name__ == "__main__":
    print(f"Generated {build_marker_icons()} marker icons in {MARKER_ICON_DIR}")

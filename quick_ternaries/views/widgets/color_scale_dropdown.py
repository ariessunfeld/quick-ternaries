# TODO: remove lazy try/except and find the problematic color scale

import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.colors import get_colorscale
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Signal

class ColorScaleDropdown(QWidget):
    """Alternative implementation using a combobox dropdown for color scale
    selection."""

    colorScaleChanged = Signal(str)  # Signal emitted when color scale changes
    _icon_cache = {}  # Cache mapping (colorscale_name, width, height) -> QIcon

    # List of standard Plotly color scales
    # TODO factor out into utils/constants or similar
    PLOTLY_COLOR_SCALES = [
        "Plotly3",
        "Viridis",
        "Cividis",
        "Inferno",
        "Magma",
        "Plasma",
        "Turbo",
        "Blackbody",
        "Bluered",
        "Electric",
        "Hot",
        "Jet",
        "Rainbow",
        "Blues",
        "BuGn",
        "BuPu",
        "GnBu",
        "Greens",
        "Greys",
        "OrRd",
        "Oranges",
        "PuBu",
        "PuBuGn",
        "PuRd",
        "Purples",
        "RdBu",
        "RdPu",
        "Reds",
        "YlGn",
        "YlGnBu",
        "YlOrBr",
        "YlOrRd",
        "turbid",
        "thermal",
        "haline",
        "solar",
        "ice",
        "gray",
        "deep",
        "dense",
        "algae",
        "matter",
        "speed",
        "amp",
        "tempo",
        "Burg",
        "Burgyl",
        "Redor",
        "Oryel",
        "Peach",
        "Pinkyl",
        "Mint",
        "Blugrn",
        "Darkmint",
        "Emrld",
        "Aggrnyl",
        "Bluyl",
        "Teal",
        "Tealgrn",
        "Purp",
        "Purpor",
        "Sunset",
        "Magenta",
        "Sunsetdark",
        "Agsunset",
        "Brwnyl",
    ]

    def __init__(self, colorscale="Viridis", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.comboBox = QComboBox()
        self.comboBox.setIconSize(QPixmap(60, 15).size())

        # Add colorscales to combobox
        for cs_name in self.PLOTLY_COLOR_SCALES:
            icon = self.create_colorscale_icon(cs_name)
            self.comboBox.addItem(icon, cs_name)

        layout.addWidget(self.comboBox)
        self.setColorScale(colorscale)
        self.comboBox.currentTextChanged.connect(self.onColorScaleSelected)

    def setColorScale(self, colorscale_name):
        """Set the color scale from its name."""
        try:
            # Find the index of the color scale in the combobox
            index = self.PLOTLY_COLOR_SCALES.index(colorscale_name)
            self.comboBox.setCurrentIndex(index)

            # Update the preview
            pixmap = self.create_colorscale_icon(colorscale_name).pixmap(80, 20)
            # self.preview.setPixmap(pixmap)

            # Store the current color scale
            self.current_colorscale = colorscale_name
        except (ValueError, IndexError) as e:
            # Default to first color scale if there's an issue
            print(f"Error setting color scale: {e}")
            if len(self.PLOTLY_COLOR_SCALES) > 0:
                self.setColorScale(self.PLOTLY_COLOR_SCALES[0])
            else:
                self.current_colorscale = "Viridis"

    def onColorScaleSelected(self, colorscale_name):
        """Handle selection of a color scale from the combobox."""
        self.setColorScale(colorscale_name)
        self.colorScaleChanged.emit(colorscale_name)

    def getColorScale(self):
        """Return the current color scale name."""
        return self.current_colorscale

    def create_colorscale_icon(self, colorscale_name, width=150, height=20):
        cache_key = (colorscale_name, width, height)
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        try:
            try:
                colorscale = get_colorscale(colorscale_name)
            except Exception:
                print(f"Failed to get colorscale for scale name {colorscale_name}")
                colorscale = [(0, "lightblue"), (0.5, "blue"), (1, "darkblue")]

            fig = make_subplots(rows=1, cols=1)
            heatmap_data = np.array([list(range(width))])
            fig.add_trace(
                go.Heatmap(z=heatmap_data, colorscale=colorscale, showscale=False)
            )
            fig.update_layout(
                width=width,
                height=height,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False,
            )
            img_bytes = fig.to_image(format="png")
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            icon = QIcon(pixmap)
            self._icon_cache[cache_key] = icon
            return icon
        except Exception as e:
            print(f"Error generating color scale icon: {e}")
            return QIcon()
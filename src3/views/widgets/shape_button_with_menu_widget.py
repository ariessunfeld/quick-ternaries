from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QMenu
)
from plotly.subplots import make_subplots
from plotly import graph_objects as go


class ShapeButtonWithMenu(QWidget):
    """Alternative implementation that uses a button + popup menu instead of a
    combobox.

    This matches the style of the ColorButton more closely.
    """

    shapeChanged = Signal(str)  # Signal emitted when shape changes
    _icon_cache = {}  # Cache for shape icons

    # List of standard Plotly marker shapes
    PLOTLY_SHAPES = [
        "circle",
        "square",
        "diamond",
        "cross",
        "x",
        "triangle-up",
        "triangle-down",
        "triangle-left",
        "triangle-right",
        "pentagon",
        "hexagon",
        "star",
        "hexagram",
        "star-triangle-up",
        "star-triangle-down",
        "star-square",
        "star-diamond",
        "diamond-tall",
        "diamond-wide",
        "hourglass",
        "bowtie",
    ]

    def __init__(self, shape="circle", parent=None):
        super().__init__(parent)

        # Create the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create the shape preview widget
        self.shapePreview = QLabel()
        self.shapePreview.setMinimumSize(24, 24)
        self.shapePreview.setMaximumSize(24, 24)
        self.shapePreview.setAlignment(Qt.AlignCenter)

        # Create the button to open the menu
        self.button = QPushButton("Select Shape")

        # Add widgets to layout
        layout.addWidget(self.shapePreview)
        layout.addWidget(self.button)

        # Create the menu but don't show it yet
        self.createMenu()

        # Set the initial shape
        self.setShape(shape)

        # Connect button click to show menu
        self.button.clicked.connect(self.showMenu)

    def createMenu(self):
        """Create the popup menu with all shape options."""
        self.menu = QMenu(self)

        # Create an action for each shape with an icon
        for shape_name in self.PLOTLY_SHAPES:
            icon = self.create_plotly_marker_icon(shape_name)
            action = QAction(icon, shape_name, self)
            action.triggered.connect(
                lambda checked=False, s=shape_name: self.onShapeSelected(s)
            )
            self.menu.addAction(action)

    def showMenu(self):
        """Show the popup menu when the button is clicked."""
        # Position the menu below the button
        pos = self.button.mapToGlobal(self.button.rect().bottomLeft())
        self.menu.popup(pos)

    def setShape(self, shape_name):
        """Set the shape from its name."""
        try:
            # Validate the shape name is in our list
            if shape_name not in self.PLOTLY_SHAPES:
                shape_name = "circle"  # Default to circle if invalid

            # Update the preview
            icon = self.create_plotly_marker_icon(shape_name)
            self.shapePreview.setPixmap(icon.pixmap(24, 24))

            # Store the current shape
            self.current_shape = shape_name
        except Exception as e:
            print(f"Error setting shape: {e}")
            # Default to circle if there's an issue
            self.current_shape = "circle"
            icon = self.create_plotly_marker_icon("circle")
            if not icon.isNull():
                self.shapePreview.setPixmap(icon.pixmap(24, 24))

    def onShapeSelected(self, shape_name):
        """Handle selection of a shape from the menu."""
        self.setShape(shape_name)
        self.shapeChanged.emit(shape_name)

    def getShape(self):
        """Return the current shape name."""
        return self.current_shape

    def create_plotly_marker_icon(self, shape, size=32):
        cache_key = (shape, size)
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]
        try:
            fig = make_subplots(rows=1, cols=1)
            fig.add_trace(
                go.Scatter(
                    x=[0],
                    y=[0],
                    mode="markers",
                    marker=dict(symbol=shape, size=size * 0.8, color="black"),
                )
            )
            fig.update_layout(
                width=size,
                height=size,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(visible=False, range=[-1, 1]),
                yaxis=dict(visible=False, range=[-1, 1]),
                showlegend=False,
            )
            img_bytes = fig.to_image(format="png")
            pixmap = QPixmap()
            pixmap.loadFromData(img_bytes)
            icon = QIcon(pixmap)
            self._icon_cache[cache_key] = icon
            return icon
        except Exception as e:
            print(f"Error generating shape icon: {e}")
            return QIcon()


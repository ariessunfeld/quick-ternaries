from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QColorDialog,
)

class ColorButton(QWidget):
    """Custom widget displaying the current color and providing a button to
    open a color picker."""

    # Signal emitted when color changes (color as hex string)
    colorChanged = Signal(str)  

    def __init__(self, color="#000000", parent=None):
        super().__init__(parent)

        # Create the layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create the color preview widget
        self.colorPreview = QLabel()
        self.colorPreview.setMinimumSize(24, 24)
        self.colorPreview.setMaximumSize(24, 24)
        self.colorPreview.setAutoFillBackground(True)

        # Create the button
        self.button = QPushButton("Select Color")

        # Add widgets to layout
        layout.addWidget(self.colorPreview)
        layout.addWidget(self.button)

        # Set the initial color
        self.setColor(color)

        # Connect the button click to open the color dialog
        self.button.clicked.connect(self.openColorDialog)

    def setColor(self, color_str):
        """Set the color from string (hex code or color name)"""
        try:
            # Try to convert the string to a QColor
            if color_str.startswith("#"):
                # Check if it's a hex code with alpha
                if len(color_str) == 9:  # Format: #AARRGGBB
                    # Extract alpha and RGB components
                    alpha_hex = color_str[1:3]
                    rgb_hex = color_str[3:9]
                    color = QColor("#" + rgb_hex)
                    color.setAlpha(int(alpha_hex, 16))
                else:
                    # Regular hex code
                    color = QColor(color_str)
            else:
                # Color name (e.g., 'red', 'blue')
                color = QColor(color_str)

            # Update the preview
            palette = self.colorPreview.palette()
            palette.setColor(QPalette.Window, color)
            self.colorPreview.setPalette(palette)

            # Store the current color with alpha information
            if color.alpha() < 255:
                # Format with alpha: #AARRGGBB where AA is alpha in hex
                alpha_hex = f"{color.alpha():02x}"
                rgb_hex = color.name()[1:]  # Remove the # from the start
                self.current_color = f"#{alpha_hex}{rgb_hex}"
            else:
                # No alpha needed, use regular hex
                self.current_color = color.name()
                
            # Store QColor object for later use
            self.qcolor = color
            
        except:
            # Default to black if there's an issue
            palette = self.colorPreview.palette()
            palette.setColor(QPalette.Window, QColor("#000000"))
            self.colorPreview.setPalette(palette)
            self.current_color = "#000000"
            self.qcolor = QColor("#000000")

    def openColorDialog(self):
        """Open the color picker dialog."""
        # Get the current color for the dialog
        initial_color = self.qcolor if hasattr(self, 'qcolor') else QColor(self.current_color)

        # Open Qt's color dialog
        color = QColorDialog.getColor(
            initial_color,
            self,
            "Select Color",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )

        # If a valid color was selected (not cancelled)
        if color.isValid():
            # Format with alpha if needed
            if color.alpha() < 255:
                alpha_hex = f"{color.alpha():02x}"
                rgb_hex = color.name()[1:]  # Remove the # from the start
                hex_color = f"#{alpha_hex}{rgb_hex}"
            else:
                hex_color = color.name()

            # Update the button
            self.setColor(hex_color)

            # Emit the signal with the new color (including alpha)
            self.colorChanged.emit(hex_color)

    def getColor(self):
        """Return the current color as string."""
        return self.current_color

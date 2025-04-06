from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
    QDoubleSpinBox
)
from PySide6.QtCore import Signal, Qt


class ColumnScalingWidget(QWidget):
    """Widget that displays selected columns for each axis/apex and allows
    setting scale factors for each column."""

    scaleChanged = Signal(str, str, float)  # axis_name, column_name, scale_factor

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.axis_sections = {}  # axis_name -> QGroupBox
        self.scale_inputs = {}  # (axis_name, column_name) -> QDoubleSpinBox

        # Add heading label
        heading = QLabel("<b>Column Scaling:</b>")
        heading.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(heading)

        # Add help text
        help_text = QLabel(
            "Set scale factors for each column. Values will be multiplied by these factors before plotting."
        )
        help_text.setWordWrap(True)
        self.layout().addWidget(help_text)

        # Add a spacer
        self.layout().addSpacing(10)

    def update_columns(self, axis_name, columns, current_scales=None):
        """Update the widget to show the current columns for an axis.

        Args:
            axis_name: Name of the axis (x_axis, y_axis, etc.)
            columns: List of column names selected for this axis
            current_scales: Dictionary of current scale values (column_name -> scale_factor)
        """
        # Default scales dictionary if none provided
        if current_scales is None:
            current_scales = {}

        # Format the axis name for display
        display_name = axis_name.replace("_", " ").title()

        # Remove the old section if it exists
        if axis_name in self.axis_sections:
            section = self.axis_sections[axis_name]
            self.layout().removeWidget(section)
            section.deleteLater()
            # Clean up scale_inputs references for this axis
            keys_to_remove = [k for k in self.scale_inputs if k[0] == axis_name]
            for key in keys_to_remove:
                del self.scale_inputs[key]
            # Remove the entry from axis_sections to ensure proper tracking
            del self.axis_sections[axis_name]

        # Create a new section if there are columns
        if columns:
            section = QGroupBox(display_name)
            section_layout = QFormLayout(section)
            section_layout.setLabelAlignment(Qt.AlignLeft)

            for column in columns:
                spin_box = QDoubleSpinBox()
                spin_box.setRange(0.01, 1000.0)  # Wide range for flexibility
                spin_box.setSingleStep(0.1)
                spin_box.setDecimals(2)  # More precision

                # Set current value from the model or default to 1.0
                scale_value = current_scales.get(column, 1.0)
                spin_box.setValue(scale_value)

                # Use a lambda that captures the current values
                def make_callback(a=axis_name, c=column):
                    return lambda value: self.scaleChanged.emit(a, c, value)

                spin_box.valueChanged.connect(make_callback())

                # Store reference to the spin box
                self.scale_inputs[(axis_name, column)] = spin_box

                # Add to layout
                section_layout.addRow(QLabel(column), spin_box)

            self.axis_sections[axis_name] = section
            self.layout().addWidget(section)

            # Force layout update
            self.layout().update()

    def set_scale_value(self, axis_name, column_name, value):
        """Set the scale value for a specific column in an axis."""
        key = (axis_name, column_name)
        if key in self.scale_inputs:
            # Block signals to prevent triggering the valueChanged signal
            self.scale_inputs[key].blockSignals(True)
            self.scale_inputs[key].setValue(value)
            self.scale_inputs[key].blockSignals(False)

    def clear(self):
        """Clear all scaling sections."""
        for section in self.axis_sections.values():
            self.layout().removeWidget(section)
            section.deleteLater()
        self.axis_sections.clear()
        self.scale_inputs.clear()
        self.layout().update()  # Force layout update after clearing


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QHBoxLayout,
    QPushButton,
)

from src3.utils.functions import (
    is_valid_formula,
    suggest_formula_from_column_name
)


class FormulaInputWidget(QWidget):
    """Widget that displays input fields for chemical formulas for each column in each axis."""

    formulaChanged = Signal(str, str, str)  # axis_name, column_name, formula

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.axis_sections = {}  # axis_name -> QGroupBox
        self.formula_inputs = {}  # (axis_name, column_name) -> QLineEdit
        self.validation_labels = {}  # (axis_name, column_name) -> QLabel

        # Add heading label
        heading = QLabel("<b>Chemical Formulas:</b>")
        heading.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout().addWidget(heading)

        # Add help text
        help_text = QLabel(
            "Enter the chemical formula for each column. These will be used for molar calculations."
        )
        help_text.setWordWrap(True)
        self.layout().addWidget(help_text)

        # Add a spacer
        self.layout().addSpacing(10)

    def update_columns(self, axis_name, columns, current_formulas=None):
        """Update the widget to show the current columns for an axis.

        Args:
            axis_name: Name of the axis (x_axis, y_axis, etc.)
            columns: List of column names selected for this axis
            current_formulas: Dictionary of current formulas (column_name -> formula)
        """
        # Default formulas dictionary if none provided
        if current_formulas is None:
            current_formulas = {}

        # Format the axis name for display
        display_name = axis_name.replace("_", " ").title()

        # Remove the old section if it exists
        if axis_name in self.axis_sections:
            section = self.axis_sections[axis_name]
            self.layout().removeWidget(section)
            section.deleteLater()
            # Clean up formula_inputs and validation_labels references for this axis
            keys_to_remove = [k for k in self.formula_inputs if k[0] == axis_name]
            for key in keys_to_remove:
                del self.formula_inputs[key]
                if key in self.validation_labels:
                    del self.validation_labels[key]
            # Remove the entry from axis_sections to ensure proper tracking
            del self.axis_sections[axis_name]

        # Create a new section if there are columns
        if columns:
            section = QGroupBox(display_name)
            form_layout = QFormLayout(section)
            form_layout.setLabelAlignment(Qt.AlignLeft)
            
            for column in columns:
                # Create a container for the formula input and validation
                input_container = QWidget()
                input_layout = QHBoxLayout(input_container)
                input_layout.setContentsMargins(0, 0, 0, 0)
                
                # Formula input field
                formula_input = QLineEdit()
                formula_input.setPlaceholderText("Enter formula (e.g. Al2O3)")
                
                # Set current value from the model or default to empty string
                formula_value = current_formulas.get(column, "")
                formula_input.setText(formula_value)
                
                # Add input to layout
                input_layout.addWidget(formula_input)
                
                # Create validation label
                validation_label = QLabel()
                validation_label.setFixedWidth(110)  # Fixed width for validation message
                validation_label.setStyleSheet("font-size: 10px;")
                input_layout.addWidget(validation_label)
                
                # Create a function to validate the formula
                def make_validator(a=axis_name, c=column, input_field=formula_input, vlabel=validation_label):
                    def validate_formula(text):
                        if not text.strip():
                            vlabel.clear()
                        elif is_valid_formula(text):
                            vlabel.setText("Valid formula")
                            vlabel.setStyleSheet("font-size: 10px; color: green;")
                        else:
                            vlabel.setText("Not a valid formula")
                            vlabel.setStyleSheet("font-size: 10px; color: red;")
                        
                        self.formulaChanged.emit(a, c, text)
                    
                    return validate_formula
                
                # Create validator function 
                validator_func = make_validator()
                
                # Connect text changed signal
                formula_input.textChanged.connect(validator_func)
                
                # Add a "Suggest" button to try auto-detecting formulas
                suggest_button = QPushButton("Suggest")
                suggest_button.setFixedWidth(70)
                input_layout.addWidget(suggest_button)
                
                # Function to suggest formula based on column name
                def make_suggester(c=column, input_field=formula_input):
                    def suggest_formula():
                        # Simple formula suggestion logic - customize as needed
                        # This would try to extract a formula from the column name
                        suggested = suggest_formula_from_column_name(c)
                        if suggested:
                            input_field.setText(suggested)
                    return suggest_formula
                
                # Connect suggest button
                suggest_button.clicked.connect(make_suggester())
                
                # Store references to the input field and validation label
                self.formula_inputs[(axis_name, column)] = formula_input
                self.validation_labels[(axis_name, column)] = validation_label
                
                # Validate initial text
                if formula_value:
                    validator_func(formula_value)
                
                # Add to form layout
                form_layout.addRow(column, input_container)

                # With this conditional version:
                if not formula_value.strip():
                    suggest_button.click()
                # suggest_button.click()

            self.axis_sections[axis_name] = section
            self.layout().addWidget(section)

            # Force layout update
            self.layout().update()

    def set_formula_value(self, axis_name, column_name, value):
        """Set the formula value for a specific column in an axis."""
        key = (axis_name, column_name)
        if key in self.formula_inputs:
            # Block signals to prevent triggering the textChanged signal
            self.formula_inputs[key].blockSignals(True)
            self.formula_inputs[key].setText(value)
            self.formula_inputs[key].blockSignals(False)
            
            # Update validation label
            if key in self.validation_labels:
                if not value.strip():
                    self.validation_labels[key].clear()
                elif is_valid_formula(value):
                    self.validation_labels[key].setText("Valid formula")
                    self.validation_labels[key].setStyleSheet("font-size: 10px; color: green;")
                else:
                    self.validation_labels[key].setText("Not a valid formula")
                    self.validation_labels[key].setStyleSheet("font-size: 10px; color: red;")

    def clear(self):
        """Clear all formula sections."""
        for section in self.axis_sections.values():
            self.layout().removeWidget(section)
            section.deleteLater()
        self.axis_sections.clear()
        self.formula_inputs.clear()
        self.validation_labels.clear()
        self.layout().update()  # Force layout update after clearing
from typing import TYPE_CHECKING


import pandas as pd
import numpy as np

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QLabel, 
    QScrollArea, 
    QFormLayout, 
    QHBoxLayout, 
    QDoubleSpinBox
)

if TYPE_CHECKING:
    from src3.models import ErrorEntryModel

class ErrorEntryWidget(QWidget):
    """
    Widget for entering uncertainty values for each component in a contour trace.
    Similar to the column scaling widget but specific to a trace.
    """
    errorChanged = Signal(str, float)  # component_name, error_value
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.error_inputs = {}  # component_name -> QDoubleSpinBox
        
        # Add header
        header = QLabel("<b>Component Uncertainties:</b>")
        header.setAlignment(Qt.AlignLeft)
        self.layout().addWidget(header)
        
        # Add help text
        help_text = QLabel(
            "Enter uncertainty values for each component. "
            "These values will be used to generate the contour."
        )
        help_text.setWordWrap(True)
        self.layout().addWidget(help_text)
        
        # Create a scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        scroll_area.setWidget(self.form_container)
        self.layout().addWidget(scroll_area)
    
    def update_components(
            self, 
            series: pd.Series, 
            error_entry_model: "ErrorEntryModel"):
        """
        Update the widget to show input fields for each component in the series.
        
        Args:
            series: The pandas Series containing the point data
            error_entry_model: The model containing current error values
        """
        # Clear existing inputs
        self.error_inputs.clear()
        
        # Clear the form layout
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if series is None or series.empty:
            # No data - show a message
            label = QLabel("No source point data available")
            label.setAlignment(Qt.AlignCenter)
            self.form_layout.addRow(label)
            return
        
        # Get the column names for each apex from the main window
        apex_columns = self._get_apex_columns()
        
        # Add inputs for each component in the series that's in an apex
        added_components = set()
        
        # First, process columns that are in apexes
        for component in series.index:
            # Skip if not numeric - uncertainty only applies to numeric values
            if not isinstance(series[component], (int, float, np.number)) or pd.isna(series[component]):
                continue
                
            # Check if this component is in any apex
            in_apex = False
            for apex_cols in apex_columns.values():
                if component in apex_cols:
                    in_apex = True
                    break
            
            if in_apex:
                self._add_component_input(component, series[component], error_entry_model)
                added_components.add(component)
        
        # If we have no components in apexes, add inputs for all numeric components
        if not added_components:
            for component in series.index:
                if isinstance(series[component], (int, float, np.number)) and not pd.isna(series[component]):
                    self._add_component_input(component, series[component], error_entry_model)
    
    def _add_component_input(
            self, 
            component: str, 
            value: float, 
            error_entry_model: "ErrorEntryModel"):
        """
        Add an input field for a component.
        
        Args:
            component: Component name
            value: The component value
            error_entry_model: The model containing current error values
        """
        # Create a container for the component with value display and input
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Show the component value
        value_label = QLabel(f"{value:.4f}")
        value_label.setMinimumWidth(60)
        container_layout.addWidget(value_label)
        
        # Add ± symbol
        container_layout.addWidget(QLabel("±"))
        
        # Create spin box for error input
        spin_box = QDoubleSpinBox()
        spin_box.setRange(0.0, 100.0)  # Reasonable range for error values
        spin_box.setSingleStep(0.1)
        spin_box.setDecimals(4)  # More precision for small values
        
        # Set current value from model
        current_error = error_entry_model.get_error(component)
        spin_box.setValue(current_error)
        
        # Connect value change
        spin_box.valueChanged.connect(
            lambda val, comp=component: self.errorChanged.emit(comp, val)
        )
        
        container_layout.addWidget(spin_box)
        container_layout.setStretchFactor(spin_box, 1)  # Give more space to the spin box
        
        # Add percentage label to make it clear we're working with absolute values
        abs_label = QLabel("(absolute)")
        container_layout.addWidget(abs_label)
        
        # Store reference to spin box
        self.error_inputs[component] = spin_box
        
        # Add to form
        self.form_layout.addRow(component, container)
    
    def _get_apex_columns(self):
        """
        Get column lists for each apex from the setup model.
        
        Returns:
            Dict mapping apex names to column lists
        """
        main_window = self.window()
        apex_columns = {
            'top_axis': [],
            'left_axis': [],
            'right_axis': []
        }
        
        if hasattr(main_window, 'setupMenuModel') and hasattr(main_window.setupMenuModel, 'axis_members'):
            axis_members = main_window.setupMenuModel.axis_members
            for apex, attr in apex_columns.items():
                if hasattr(axis_members, apex):
                    apex_columns[apex] = getattr(axis_members, apex)
        
        return apex_columns
    
    def get_error_value(self, component: str) -> float:
        """
        Get the current error value for a component.
        
        Args:
            component: Component name
            
        Returns:
            Current error value
        """
        if component in self.error_inputs:
            return self.error_inputs[component].value()
        return 0.0
    
    def set_error_value(self, component: str, value: float):
        """
        Set the error value for a component.
        
        Args:
            component: Component name
            value: Error value
        """
        if component in self.error_inputs:
            self.error_inputs[component].setValue(value)

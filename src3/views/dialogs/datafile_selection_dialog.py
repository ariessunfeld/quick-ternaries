
from PySide6.QtWidgets import (
    QDialog, 
    QVBoxLayout, 
    QLabel, 
    QComboBox,
    QGroupBox, 
    QListWidget, 
    QListWidgetItem, 
    QDialogButtonBox
)
from PySide6.QtGui import QColor

class DatafileSelectionDialog(QDialog):
    """Dialog for selecting a datafile with validation of impacts."""
    
    def __init__(self, parent=None, current_datafile=None, all_datafiles=None):
        super().__init__(parent)
        self.setWindowTitle("Select Datafile")
        self.resize(600, 400)  # Slightly larger for better impact display
        
        # Store the current and available datafiles
        self.current_datafile = current_datafile
        self.all_datafiles = all_datafiles or []
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Add info label
        info_label = QLabel("Select a datafile for this trace:")
        info_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(info_label)
        
        # Create datafile combobox
        self.datafile_combo = QComboBox()
        self.datafile_combo.setMinimumWidth(450)
        
        # Populate combobox with datafile display strings
        for datafile in self.all_datafiles:
            display_str = str(datafile)
            self.datafile_combo.addItem(display_str)
        
        # Set current datafile if provided
        if current_datafile:
            current_display_str = str(current_datafile)
            index = self.datafile_combo.findText(current_display_str)
            if index >= 0:
                self.datafile_combo.setCurrentIndex(index)
        
        main_layout.addWidget(self.datafile_combo)
        
        # Add spacer
        main_layout.addSpacing(10)
        
        # Add impact display area
        self.impact_group = QGroupBox("Potential Impacts")
        self.impact_group.setVisible(False)  # Initially hidden
        impact_layout = QVBoxLayout(self.impact_group)
        
        self.impact_label = QLabel("The following changes will be made:")
        impact_layout.addWidget(self.impact_label)
        
        self.impact_list = QListWidget()
        self.impact_list.setAlternatingRowColors(True)
        impact_layout.addWidget(self.impact_list)
        
        main_layout.addWidget(self.impact_group)
        
        # Add warning message for critical impacts
        self.warning_label = QLabel()
        self.warning_label.setStyleSheet("color: red; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        self.warning_label.setVisible(False)
        main_layout.addWidget(self.warning_label)
        
        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Connect combobox change signal
        self.datafile_combo.currentIndexChanged.connect(self.on_selection_changed)
        
        # Store impacts for each datafile option
        self.potential_impacts = {}  # index -> (impacts, has_critical)
        
        # Selected datafile (to be returned)
        self.selected_datafile = None
        self.impacts = []
    
    def on_selection_changed(self, index):
        """When user selects a different datafile, display pre-calculated impacts."""
        if index < 0 or index >= len(self.all_datafiles):
            return
        
        # Clear previous impacts
        self.impact_list.clear()
        self.impacts = []
        
        # Get the selected datafile
        selected = self.all_datafiles[index]
        
        # If it's the same as current, no impacts
        if selected == self.current_datafile:
            self.impact_group.setVisible(False)
            self.warning_label.setVisible(False)
            return
        
        # Otherwise, check for pre-calculated impacts
        if index in self.potential_impacts:
            impacts, has_critical = self.potential_impacts[index]
            self.set_impacts(impacts, has_critical)
        else:
            # No pre-calculated impacts, hide the impact group
            self.impact_group.setVisible(False)
            self.warning_label.setVisible(False)
        
        # Store the selected datafile for return
        self.selected_datafile = selected
        
    def set_impacts(self, impacts, has_critical=False):
        """Set the list of impacts to display to the user."""
        self.impacts = impacts
        
        # Update impact list
        # TODO make this logic much better, e.g. use a dictionary to map severity to color
        # Very fragile right now, relying on these emojis
        self.impact_list.clear()
        for impact in impacts:
            # Use different colors based on impact severity
            item = QListWidgetItem(impact)
            if "🔴" in impact:
                item.setForeground(QColor("red"))
            elif "🔶" in impact:
                item.setForeground(QColor("orange"))
            self.impact_list.addItem(item)
        
        # Show/hide impact group based on whether there are impacts
        self.impact_group.setVisible(len(impacts) > 0)
        
        # Show/hide warning label based on critical impacts
        self.warning_label.setVisible(has_critical)
        if has_critical:
            self.warning_label.setText(
                "WARNING: The selected datafile will cause significant changes to your trace configuration. "
                "Some columns or filters may be reset to default values."
            )
    
    def get_selected_datafile(self):
        """Get the datafile selected by the user."""
        if self.result() == QDialog.Accepted:
            index = self.datafile_combo.currentIndex()
            if 0 <= index < len(self.all_datafiles):
                return self.all_datafiles[index]
        return None

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from quick_ternaries.controllers import TraceEditorController
    from quick_ternaries.app import MainWindow

from PySide6.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QSizePolicy, 
    QPushButton, 
    QDialog
)
from PySide6.QtCore import Signal, Qt

from quick_ternaries.views.widgets import ScrollableLabel
from quick_ternaries.views.dialogs import DatafileSelectionDialog


class DatafileSelector(QWidget):
    """
    Displays a horizontally scrollable, read-only text field for the current datafile,
    plus an ellipsis button to open a selection dialog.
    """
    datafileChanged = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main layout with better alignment control
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignVCenter)  # Important - align everything vertically
        
        # Our scrollable label widget
        self.display = ScrollableLabel()
        self.display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.display, 0, Qt.AlignVCenter)  # Force vertical centering
        
        # The ellipsis button with consistent height
        self.change_button = QPushButton("...")
        self.change_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.change_button.setToolTip("Select Datafile")
        self.change_button.setFixedHeight(28)  # Match ScrollableLabel exactly
        self.change_button.setFixedWidth(28)   # Square button looks nicer
        
        # Optional: Style the button to match the label's appearance
        self.change_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                background-color: rgba(240, 240, 240, 0.5);
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.change_button, 0, Qt.AlignVCenter)  # Force vertical centering
        
        # Connect button click
        self.change_button.clicked.connect(self.open_selection_dialog)
        
        # Set a fixed height for the entire widget to ensure consistent rendering
        self.setFixedHeight(30)  # Slightly larger to contain everything
        
        # Internal state
        self._datafile = None
        self._all_datafiles = []
        self.main_window = None

    def setDatafile(self, datafile):
        """Set the current datafile and update the display."""
        self._datafile = datafile
        if datafile:
            text = str(datafile)
            self.display.setText(text)
            # Scroll to the end
            hbar = self.display.scroll_area.horizontalScrollBar()
            hbar.setValue(hbar.maximum())
            self.display.setToolTip(text)
        else:
            self.display.setText("No datafile selected")
            self.display.setToolTip("")

    def datafile(self):
        """Return the currently set datafile."""
        return self._datafile

    def setAllDatafiles(self, datafiles):
        """Set the list of available datafiles."""
        self._all_datafiles = datafiles

    def setMainWindow(self, main_window: "MainWindow"):
        """Set a reference to the main window (used to access the controller)."""
        self.main_window = main_window

    def open_selection_dialog(self):
        """Open a dialog for selecting a new datafile and update impacts if applicable."""
        if not self.main_window:
            print("Warning: Main window reference not set in DatafileSelector")
            return

        # Create the selection dialog (assumed to be defined elsewhere)
        dialog = DatafileSelectionDialog(
            self,
            current_datafile=self._datafile,
            all_datafiles=self._all_datafiles
        )

        # (Optional) Pre-calculate impacts for each potential datafile if available
        if hasattr(self.main_window, "traceEditorController"):
            controller = self.main_window.traceEditorController
            for i in range(dialog.datafile_combo.count()):
                try:
                    potential_datafile = self._all_datafiles[i]
                    if potential_datafile != self._datafile:
                        impacts, has_critical = controller.calculate_datafile_change_impacts(potential_datafile)
                        dialog.potential_impacts[i] = (impacts, has_critical)
                except Exception as e:
                    import traceback
                    print(f"Error calculating impacts for datafile at index {i}: {e}")
                    traceback.print_exc()
                    dialog.potential_impacts[i] = ([f"Error analyzing impacts: {str(e)}"], True)

            # Ensure that impacts for the current selection are shown
            current_index = dialog.datafile_combo.currentIndex()
            try:
                dialog.on_selection_changed(current_index)
            except Exception as e:
                import traceback
                print(f"Error displaying impacts for current selection: {e}")
                traceback.print_exc()

        # Show the dialog and update the datafile if the user accepts
        try:
            result = dialog.exec()
            if result == QDialog.Accepted:
                new_datafile = dialog.get_selected_datafile()
                if new_datafile and new_datafile != self._datafile:
                    self.setDatafile(new_datafile)
                    self.datafileChanged.emit(new_datafile)
                    print(f"Datafile changed to: {new_datafile}")
                else:
                    print("No change in datafile - keeping current selection")
        except Exception as e:
            import traceback
            print(f"Error in datafile selection dialog: {e}")
            traceback.print_exc()

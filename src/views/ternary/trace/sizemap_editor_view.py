"""View for the Sizemap configuration"""


from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QButtonGroup
)
from PySide6.QtCore import Qt

from src.views.utils import (
    LeftLabeledLineEdit,
    LeftLabeledComboBox,
    InfoButton,
    LeftLabeledCheckbox,
    LeftLabeledRadioButton,
    LeftLabeledImageComboBox,
    LeftLabeledFontComboBox,
    LeftLabeledSpinBox
)

from src.services.utils.sequential_color_scales import SEQUENTIAL_COLOR_SCALE_NAMES

class TernarySizemapEditorView(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()

        # Create a container widget to hold the main layout
        self.container_widget = QWidget()
        self.container_widget.setObjectName("containerWidget")  # Set an object name
        self.container_layout = QVBoxLayout()
        self.container_widget.setLayout(self.container_layout)
        
        # add a border to the container widget
        self.container_widget.setStyleSheet("#containerWidget { border: 1px solid #1c1c1c; }")
        
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.container_widget)

        # Heatmap Column ComboBox
        self.sizemap_column_combobox = LeftLabeledComboBox('Sizemap Column:')
        self.container_layout.addWidget(self.sizemap_column_combobox)

        # Range Min and Max LineEdits with an InfoButton
        self.range_layout = QHBoxLayout()
        
        self.range_min_line_edit = LeftLabeledLineEdit('Min size:')
        self.range_layout.addWidget(self.range_min_line_edit)
        
        self.range_max_line_edit = LeftLabeledLineEdit('Max size:')
        self.range_layout.addWidget(self.range_max_line_edit)

        # Tooltip InfoButton
        tooltip_text = (
            "Tip: Set a higher 'max size' to bring out the gradient in your data.")
        self.info_button = InfoButton(self, tooltip_text)
        self.range_layout.addWidget(self.info_button, alignment=Qt.AlignRight)
        
        # Add the range layout to the view
        self.container_layout.addLayout(self.range_layout)

        # Create the Advanced... checkbox
        self.show_advanced_checkbox = LeftLabeledCheckbox('Show Advanced Settings...')
        
        # Add to the main layout
        self.container_layout.addWidget(self.show_advanced_checkbox)

        # Set up the advanced options layout and add to main
        self.advanced_options_layout = QVBoxLayout()
        self.advanced_options_layout_widget = QWidget()
        self.advanced_options_layout_widget.setLayout(self.advanced_options_layout)
        self.advanced_options_layout_widget.setVisible(False)
        self.container_layout.addWidget(self.advanced_options_layout_widget)

        # Add some advanced options
        self.log_transform_checkbox = LeftLabeledCheckbox("Log-Transform Range:")
        self.log_and_reverse_layout = QHBoxLayout()
        self.log_and_reverse_layout.addWidget(self.log_transform_checkbox)

        self.advanced_options_layout.addLayout(self.log_and_reverse_layout)

        # Make a layout for `sorting` options
        self.radio_group_box = QGroupBox("Data Sorting")
        self.radio_layout = QGridLayout(self.radio_group_box)

        self.high_on_top_radio = LeftLabeledRadioButton("High on top")
        self.low_on_top_radio = LeftLabeledRadioButton("Low on top")
        self.shuffled_radio = LeftLabeledRadioButton("Shuffled")
        self.no_change_radio = LeftLabeledRadioButton('No change')

        # Add buttons to a button group for mutex
        self.data_sorting_radiobutton_group = QButtonGroup(self)
        self.data_sorting_radiobutton_group.addButton(self.high_on_top_radio.radio_button)
        self.data_sorting_radiobutton_group.addButton(self.low_on_top_radio.radio_button)
        self.data_sorting_radiobutton_group.addButton(self.shuffled_radio.radio_button)
        self.data_sorting_radiobutton_group.addButton(self.no_change_radio.radio_button)

        # Add the radio buttons to the layout
        self.radio_layout.addWidget(self.high_on_top_radio, 1, 0)
        self.radio_layout.addWidget(self.low_on_top_radio, 1, 1)
        self.radio_layout.addWidget(self.shuffled_radio, 0, 1)
        self.radio_layout.addWidget(self.no_change_radio, 0, 0)

        # Add the group box to the main layout
        self.advanced_options_layout.addWidget(self.radio_group_box)

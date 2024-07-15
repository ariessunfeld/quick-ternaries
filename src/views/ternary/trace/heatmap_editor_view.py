"""Megawidget for heatmap configuration within a trace"""

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

class TernaryHeatmapEditorView(QWidget):
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
        self.heatmap_column_combobox = LeftLabeledComboBox('Heatmap Column:')
        self.container_layout.addWidget(self.heatmap_column_combobox)

        # Range Min and Max LineEdits with an InfoButton
        self.range_layout = QHBoxLayout()
        
        self.range_min_line_edit = LeftLabeledLineEdit('Range min:')
        self.range_layout.addWidget(self.range_min_line_edit)
        
        self.range_max_line_edit = LeftLabeledLineEdit('Range max:')
        self.range_layout.addWidget(self.range_max_line_edit)

        # Tooltip InfoButton
        tooltip_text = (
            "Tip: Set a low 'range max' to bring out the gradient in your data.\n"
            "Points with higher values than 'range max' will still be plotted; \n"
            "they will just have the same color as the highest value on the scale.\n"
            "The default 'range max' value is twice the median of the selected column."
        )
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
        self.heatmap_colorscale_combobox = LeftLabeledImageComboBox('Colorscale:')
        self.heatmap_colorscale_combobox.addColorscaleIcons(SEQUENTIAL_COLOR_SCALE_NAMES)
        self.log_transform_checkbox = LeftLabeledCheckbox("Log-Transform Range:")
        self.reverse_colorscale_checkbox = LeftLabeledCheckbox("Reverse Colorscale:")
        self.log_and_reverse_layout = QHBoxLayout()
        self.log_and_reverse_layout.addWidget(self.log_transform_checkbox)
        self.log_and_reverse_layout.addWidget(self.reverse_colorscale_checkbox)

        self.advanced_options_layout.addWidget(self.heatmap_colorscale_combobox)
        self.advanced_options_layout.addLayout(self.log_and_reverse_layout)

        self.title_configuration_layout = QHBoxLayout()
        self.title_line_edit = LeftLabeledLineEdit("Bar Title:")
        self.title_position_combobox = LeftLabeledComboBox("Title Position:")
        self.title_position_combobox.addItems(['right', 'left', 'top', 'bottom'])

        self.title_configuration_layout.addWidget(self.title_line_edit)
        self.title_configuration_layout.addWidget(self.title_position_combobox)

        self.advanced_options_layout.addLayout(self.title_configuration_layout)

        # Make a layout for additional fields (orientation and font)
        self.orientation_and_font_layout = QGridLayout()
        self.colorbar_font_line_edit = LeftLabeledFontComboBox("Font:")
        self.colorbar_orientation_combobox = LeftLabeledComboBox("Bar:")
        self.colorbar_orientation_combobox.addItems(['vertical', 'horizontal'])
        self.colorbar_title_font_size_line_edit = LeftLabeledSpinBox("Title Font Size:")
        self.colorbar_title_font_size_line_edit.setMinimum(1)
        self.colorbar_tick_font_size_line_edit = LeftLabeledSpinBox("Tick Font Size:")
        self.colorbar_tick_font_size_line_edit.setMinimum(1)
        self.orientation_and_font_layout.addWidget(self.colorbar_font_line_edit, 0, 0)
        self.orientation_and_font_layout.addWidget(self.colorbar_orientation_combobox, 0, 1)
        self.orientation_and_font_layout.addWidget(self.colorbar_title_font_size_line_edit, 1, 0)
        self.orientation_and_font_layout.addWidget(self.colorbar_tick_font_size_line_edit, 1, 1)

        # Add to the main advanced config layout
        self.advanced_options_layout.addLayout(self.orientation_and_font_layout)

        # Make an arrea for position and dimensions
        self.position_dimensions_groupbox = QGroupBox('Position && Dimensions')
        self.position_dimensions_layout = QHBoxLayout()

        # Create the grid layout for the first four fields
        self.position_dimensions_grid_layout = QGridLayout()
        self.len_line_edit = LeftLabeledLineEdit('len:')
        self.thickness_line_edit = LeftLabeledLineEdit('thickness:')
        self.x_line_edit = LeftLabeledLineEdit('x:')
        self.y_line_edit = LeftLabeledLineEdit('y:')

        position_dimensions_tooltip_text = (
            "len = 1 will make colorbar as long as the plot.\n"
            "x > 1 will position colorbar to the right of the plot.\n"
            "x < 0 will position colorbar to the left of the plot.\n"
            "y = 0.5 will center the colorbar with respect to the plot height."
        )
        self.position_dimensions_infobutton = InfoButton(self, position_dimensions_tooltip_text)

        # Add position/dimensions fields to their layout
        self.position_dimensions_grid_layout.addWidget(self.len_line_edit, 1, 0)
        self.position_dimensions_grid_layout.addWidget(self.thickness_line_edit, 1, 1)
        self.position_dimensions_grid_layout.addWidget(self.x_line_edit, 0, 0)
        self.position_dimensions_grid_layout.addWidget(self.y_line_edit, 0, 1)

        # Create the vertical layout for the info button
        self.position_dimensions_tooltip_layout = QVBoxLayout()
        self.position_dimensions_tooltip_layout.addStretch()
        self.position_dimensions_tooltip_layout.addWidget(self.position_dimensions_infobutton)
        self.position_dimensions_tooltip_layout.addStretch()

        # Add the grid layout and the vertical layout to the main layout
        self.position_dimensions_layout.addLayout(self.position_dimensions_grid_layout, 3)
        self.position_dimensions_layout.addLayout(self.position_dimensions_tooltip_layout, 1)

        # Set the main layout to the group box
        self.position_dimensions_groupbox.setLayout(self.position_dimensions_layout)

        # Add the group box to the advanced options layout
        self.advanced_options_layout.addWidget(self.position_dimensions_groupbox)

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

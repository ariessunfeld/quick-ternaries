"""Contains the MainWindow(QWidget) view class, which encompasses the navigation panel, dynamic content area, preview/save buttons, and plot view area"""

import os

from PySide6.QtWidgets import (
    QMainWindow,
    QStackedWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSizePolicy,
    QFileDialog,
    QInputDialog,
    QApplication,
    QMessageBox,
    QScrollArea
)

from PySide6.QtCore import (
    Qt, 
    QRect, 
    QSize, 
    QUrl, 
    QTimer, 
    Slot
)

from PySide6.QtGui import (
    QIcon,
    QFontDatabase, 
    QFont, 
    QDesktopServices, 
    QPalette, 
    QMovie
)

from PySide6.QtWebEngineWidgets import QWebEngineView

from src.views.ternary.setup.view import TernarySetupMenu
from src.views.ternary.trace.view import TernaryTraceEditor
from src.views.ternary.trace.trace_scroll_area import TabView
from src.views.utils import (
    CustomSplitter,
    GifPopup,
    PushButton
)
from src.views.components import LoadedDataScrollView

from src.services.utils.plotly_interface import PlotlyInterface


class MainWindow(QMainWindow):

    # TODO eventually move these paths into a config module
    # update the paths accordingly
    BLANK_TERNARY_PATH = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'resources', 
        'blank_ternary_plot.html')
    
    BLANK_CARTESIAN_PATH = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'resources', 
        'blank_cartesian_plot.html')
    
    TERNARY_BOOTSTRAP_TUTORIAL_PATH = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'resources', 
        'bootstrap-tutorial.gif')
    
    TITLE_FONT = os.path.join(
        os.path.dirname(__file__),
        '..',
        'assets',
        'fonts',
        'Motter_Tektura_Normal.ttf')
    
    DEFAULT_PLOT_FONT = os.path.join(
        os.path.dirname(__file__),
        '..',
        'assets',
        'fonts',
        'OpenSans-Regular.ttf')
    
    # Dict of plot types 
    # keys used to populate plot type combobox
    # values used to get plot-specific views
    PLOT_TYPES = {
        
        # ---- General ----

        "Ternary": 'ternary', 
        "Cartesian": 'cartesian', 
        # "Correlation Plot": 'corrplot',
        # "Area Chart": 'area_chart',
        # "Rose Plot": 'roseplot,

        # ---- Special ----

        # "ZMap": 'zmap', 
        # "Depth Profile: 'depth_profile"

    }
    
    def __init__(self):
        super().__init__()

        self.setupFonts()

        self.setWindowTitle("Quick Ternaries")

        self.plotly_interface = PlotlyInterface()

        # Top Bar
        self.top_bar = QHBoxLayout()
        self.app_name_label = self.setup_title("quick ternaries")
        self.settings_button = self.create_settings_button()

        # Bottom Bar
        self.bottom_bar = QHBoxLayout()
        self.preview_button = PushButton("Preview")
        self.save_button = PushButton("Save")
        self.bootstrap_button = PushButton("Bootstrap")
        
        # disable previewing and saving upon initialization
        self.preview_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.bootstrap_button.setEnabled(False)
        
        # Plotting mode selection box
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(self.PLOT_TYPES.keys())
        
        # Add widgets to top bar
        self.top_bar.addWidget(self.app_name_label)
        self.top_bar.addStretch(1)
        self.top_bar.addWidget(self.plot_type_combo)
        self.top_bar.addWidget(self.settings_button)

        # Add widgets to bottom bar
        self.bottom_bar.addWidget(self.preview_button)
        self.bottom_bar.addWidget(self.save_button)
        self.bottom_bar.addWidget(self.bootstrap_button)
        self.bottom_bar.addStretch(1)

        # Left Scroll Area for Trace Tabs
        self.tab_view = TabView()

        # Dynamic content area for switching between Setup Menu and Trace Editor
        self.changed_tab_stack = QStackedWidget()

        # Dynamic content area for switching between various Setup Menus
        self.setup_menu_inner_stack = QStackedWidget()

        # Megawidget for loaded data and Setup Menus(s)
        self.setup_menu_widget = QWidget()
        self.setup_menu_layout = QVBoxLayout()
        self.setup_menu_widget.setLayout(self.setup_menu_layout)

        # Scroll area to display filenames for loaded data
        self.loaded_data_scroll_view = LoadedDataScrollView()
        self.setup_menu_layout.addWidget(self.loaded_data_scroll_view, 1)
        self.setup_menu_layout.addWidget(self.setup_menu_inner_stack, 3)

        # Specific plot-type setup menu and trace editor views

        self.ternary_setup_menu = TernarySetupMenu()
        self.ternary_trace_editor = TernaryTraceEditor()

        # ----------------------------------------

        # self.cartesian_setup_menu = CartesianSetupMenu()
        # self.cartesian_trace_editor = CartesianTraceEditor()

        # self.corrplot_setup_menu = CorrplotSetupMenu()
        # self.corrplot_trace_editor = CorrplotTraceEditor()
        
        # self.zmap_setup_menu = ZmapSetupMenu()
        # self.zmap_trace_editor = ZmapTraceEditor()
        
        # self.depth_profile_setup_menu = DepthProfileSetupMenu()
        # self.depth_profile_trace_editor = DepthProfileTraceEditor()
        
        # self.area_chart_setup_menu = AreaChartSetupMenu()
        # self.area_chart_trace_editor = AreaChartTraceEditor()

        # self.roseplot_setup_menu = RoseplotSetupMenu()
        # self.roseplot_trace_editor = RoseplotTraceEditor()

        # ----------------------------------------
        
        # Add the generic setup menu widget to the changed tab stack
        # This widget contains the loaded data area and the setup menu inner stack
        self.changed_tab_stack.addWidget(self.setup_menu_widget)

        # Add the plot type trace editors to the changed tab stack
        self.changed_tab_stack.addWidget(self.ternary_trace_editor)
        # self.changed_tab_stack.addWidget(self.cartesian_trace_editor)
        # self.changed_tab_stack.addWidget(self.corrplot_trace_editor)
        # self.changed_tab_stack.addWidget(self.zmap_trace_editor)
        # self.changed_tab_stack.addWidget(self.depth_profile_trace_editor)
        # self.changed_tab_stack.addWidget(self.area_chart_trace_editor)
        # self.changed_tab_stack.addWidget(self.roseplot_trace_editor)

        # Add the plot type setup menus to the setup menu inner stack
        self.setup_menu_inner_stack.addWidget(self.ternary_setup_menu)
        # self.setup_menu_inner_stack.addWidget(self.cartesian_setup_menu)
        # self.setup_menu_inner_stack.addWidget(self.corrplot_setup_menu)
        # self.setup_menu_inner_stack.addWidget(self.zmap_setup_menu)
        # self.setup_menu_inner_stack.addWidget(self.depth_profile_setup_menu)
        # self.setup_menu_inner_stack.addWidget(self.area_chart_setup_menu)
        # self.setup_menu_inner_stack.addWidget(self.roseplot_setup_menu)
        
        # Start the changed tab stack on setup menu widget
        # Start the inner stack on the ternary setup menu
        self.changed_tab_stack.setCurrentWidget(self.setup_menu_widget)
        self.setup_menu_inner_stack.setCurrentWidget(self.ternary_setup_menu)

        # Right Area for displaying Plotly Plot (using QWebEngineView)
        self.plot_view = QWebEngineView()
        self.plot_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Encapsulate QWebEngineView within a QScrollArea
        self.plot_scroll_area = QScrollArea()
        self.plot_scroll_area.setWidget(self.plot_view)
        self.plot_scroll_area.setWidgetResizable(True)
        self.plot_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Load local HTML file
        self.display_blank_ternary_plot()

        # Add a splitter so user can drag the plot area to resize horizontally
        self.main_splitter = CustomSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.changed_tab_stack)
        self.main_splitter.addWidget(self.plot_scroll_area)

        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.tab_view, 1)
        self.main_layout.addWidget(self.main_splitter, 6)

        # Combine Top Bar and Main Layout
        self.central_layout = QVBoxLayout()
        self.central_layout.addLayout(self.top_bar)
        self.central_layout.addLayout(self.main_layout)
        self.central_layout.addLayout(self.bottom_bar)

        # Set central widget
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.central_layout)
        self.setCentralWidget(self.central_widget)

        # Handle dark/light-mode changes while app is running
        QApplication.instance().paletteChanged.connect(self.on_palette_changed)

    def setupFonts(self):
        """
        Adds fonts (eg Open Sans) to the set of recognized application fonts
        """
        font_path = self.DEFAULT_PLOT_FONT
        QFontDatabase.addApplicationFont(font_path)

    @Slot()
    def on_palette_changed(self):
        """
        Slot that is called when the application's palette changes.
        """
        QTimer.singleShot(750, lambda: self.update_title_view("quick ternaries"))

    def switch_to_start_setup_view(self):
        self.changed_tab_stack.setCurrentWidget(self.ternary_setup_menu)
    
    def switch_to_trace_view(self):
        self.changed_tab_stack.setCurrentWidget(self.ternary_trace_editor)

    def switch_to_standard_trace_view(self):
        self.switch_to_trace_view()
        self.ternary_trace_editor.switch_to_standard_view()
    
    def switch_to_bootstrap_trace_view(self):
        self.switch_to_trace_view()
        self.ternary_trace_editor.switch_to_bootstrap_view()

    # def switch_plot_type(self, index):
    #     plot_type = self.plot_type_combo.itemText(index)
    #     # Logic to switch plot type goes here
    #     print(f"Switched to plot type: {plot_type}")

    def show_save_menu(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_types = "PNG Files (*.png);;JPEG Files (*.jpg);;SVG Files (*.svg);;PDF Files (*.pdf);;HTML Files (*.html)"
        filepath, selected_filter = QFileDialog.getSaveFileName(
            self, 
            "Save Diagram", 
            "",
            file_types, 
            options=options)

        if '.' not in filepath.split("/")[-1]:
            extension = selected_filter.split("(*")[1].split(")")[0]  # Extract the extension
            filepath += extension

        if not filepath.endswith('.html'):
            # Prompt for DPI
            dpi, _ = QInputDialog.getInt(self, "DPI Setting", "Enter DPI:", 400, 1, 10000)
        else:
            dpi = None

        return filepath, dpi

    # TODO refactor these two methods into a single display_blank_plot(self) method
    # that looks up the current plot type and display the correct one
    def display_blank_ternary_plot(self):
        url = QUrl.fromLocalFile(self.BLANK_TERNARY_PATH)
        self.plot_view.setUrl(url)

    def display_blank_cartesian_plot(self):
        url = QUrl.fromLocalFile(self.BLANK_CARTESIAN_PATH)
        self.plot_view.setUrl(url)

    def show_bootstrap_tutorial_gif(self):
        tutorial_gif = self.TERNARY_BOOTSTRAP_TUTORIAL_PATH
        msg = "Use the Lasso tool in the top-right of the ternary\nplot window to select a single point.\n\n"
        msg += "Then click `Bootstrap` to configure an uncertainty\ncontour around this point.\n\n"
        msg += "Ensure that only a single point is selected with the lasso."
        gif_popup = GifPopup(tutorial_gif, 400, 300, msg, self)
        gif_popup.setGeometry(QRect(50, 50, 400, 300))  # Adjust size to accommodate text and GIF
        gif_popup.show()

    def setup_title(self, title: str):
        """
        Load the 'Motter Tektura' font and use it to set up the application's title label.
        The title label is configured to display the 'quick ternaries' logo which includes a
        hyperlink to the project repository.
        """
        font_path = self.TITLE_FONT
        font_id = QFontDatabase.addApplicationFont(font_path)
        self.title_label = QLabel()
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                custom_font = QFont(font_families[0], pointSize=20)
                self.title_label.setFont(custom_font)
        self.update_title_view(title)
        self.title_label.linkActivated.connect(lambda link: QDesktopServices.openUrl(QUrl(link)))
        self.title_label.setOpenExternalLinks(True)  # Allow the label to open links
        return self.title_label

    def update_title_view(self, title: str):
        """
        Update the title label hyperlink color based on the current theme.
        """
        self.title_label.setText(
            '<a href=https://github.com/ariessunfeld/quick-ternaries ' +
            f'style="color: {self.get_title_color()}; text-decoration:none;">' +
            f'{title}' +
            '</a>'
        )

    def get_title_color(self):
        """
        Determine the appropriate title color based on the current palette.
        """
        palette = self.palette()
        background_color = palette.color(QPalette.Window)
        is_dark_mode = background_color.value() < 128  # Assuming dark mode if background is dark
        return 'white' if is_dark_mode else 'black'

    def create_settings_button(self):
        button = QPushButton(self)
        button.setStyleSheet('border: none;')
        button.setIconSize(QSize(20, 20))
        button.setFixedSize(20, 20)
        button.setCursor(Qt.PointingHandCursor)
        self.updateSettingsIcon(button)
        return button

    def updateSettingsIcon(self, button):
        """
        Update the settings icon based on the current theme.
        """
        settings_gear_icon = os.path.join(
            os.path.dirname(__file__),
            '..',
            'assets',
            'icons',
            'settings_icon.png')
        icon = QIcon(settings_gear_icon)
        button.setIcon(icon)

    def update_font(self, font):
        self.setFont(font)
        for widget in self.findChildren(QWidget):
            widget.setFont(font)

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Quit Confirmation',
                                     "Are you sure you want to quit?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

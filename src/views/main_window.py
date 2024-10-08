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
    QScrollArea,
    QSplitter,
    QSplitterHandle
)

from PySide6.QtCore import Qt, QRect, QSize, QUrl, QTimer, Slot
from PySide6.QtGui import QColor, QIcon, QFontDatabase, QFont, QDesktopServices, QPalette, QMovie
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QPainter, QPen

from src.views.ternary.setup.view import TernaryStartSetupView
from src.views.ternary.trace.view import TernaryTraceEditorView
from src.views.ternary.trace.trace_scroll_area import TabView

from src.services.utils.plotly_interface import PlotlyInterface

# Disable the qt.pointer.dispatch debug messages
os.environ["QT_LOGGING_RULES"] = "qt.pointer.dispatch=false;qt.webengine.*=false"


class CustomSplitterHandle(QSplitterHandle):
    def __init__(self, orientation, parent):
        super().__init__(orientation, parent)
        self.setCursor(Qt.SplitHCursor)  # Set the cursor to a horizontal split cursor

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set the color and pen for drawing
        pen = QPen(QColor('#999999'))
        pen.setWidth(2)
        painter.setPen(pen)

        # Draw vertical lines or arrows for horizontal splitters
        mid_x = self.width() // 2 - 2
        painter.drawLine(mid_x, 0, mid_x, self.height())
        # painter.drawLine(mid_x - 3, 5, mid_x, 0)
        # painter.drawLine(mid_x + 3, 5, mid_x, 0)

class CustomSplitter(QSplitter):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)

    def createHandle(self):
        return CustomSplitterHandle(self.orientation(), self)
    

class GifPopup(QWidget):
    def __init__(self, gif_path, width, height, text, parent=None):
        super(GifPopup, self).__init__(parent)
        self.setWindowFlag(Qt.Popup)

        self.text_label = QLabel(text, self)
        self.gif_label = QLabel(self)
        self.movie = QMovie(gif_path)
        self.movie.setScaledSize(QSize(width, height))
        self.gif_label.setMovie(self.movie)
        self.gif_label.setFixedSize(width, height)

        layout = QHBoxLayout()
        layout.addWidget(self.text_label)
        layout.addWidget(self.gif_label)
        self.setLayout(layout)

        self.movie.start()


class MainWindow(QMainWindow):

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
        self.preview_button = QPushButton("Preview")
        self.save_button = QPushButton("Save")
        self.bootstrap_button = QPushButton("Bootstrap")

        # switch to pointing hand cursor when hovering over buttons
        self.preview_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.bootstrap_button.setCursor(Qt.PointingHandCursor)
        
        # disable previewing and saving upon initialization
        self.preview_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.bootstrap_button.setEnabled(False)
        
        # Plotting mode selection box
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Ternary", "Cartesian", "ZMap", "Depth Profile"])
        #self.plot_type_combo.currentIndexChanged.connect(self.switch_plot_type)
        
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

        # Dynamic Content Area
        self.dynamic_content_area = QStackedWidget()
        self.ternary_start_setup_view = TernaryStartSetupView()
        self.ternary_trace_editor_view = TernaryTraceEditorView()
        # We will then have classes for CartesianTraceView, ZMapTraceView, etc.
        # In these classes we can have the trace-level customization options for these other plot modes
        # This might involve a file tree refactor where now we have src.views.ternary.start_setup and src.views.ternary.trace
        # Will have to think about how we handle controllers etc, maybe the app has a "main controller" which changes for diff plot modes
        self.dynamic_content_area.addWidget(self.ternary_start_setup_view)
        self.dynamic_content_area.addWidget(self.ternary_trace_editor_view)
        self.dynamic_content_area.setCurrentWidget(self.ternary_start_setup_view)

        # Right Area for Plotly Plot (using QWebEngineView)
        self.plot_view = QWebEngineView()
        self.plot_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Encapsulate QWebEngineView within a QScrollArea
        self.plot_scroll_area = QScrollArea()
        self.plot_scroll_area.setWidget(self.plot_view)
        self.plot_scroll_area.setWidgetResizable(True)
        self.plot_scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Load local HTML file
        self.switch_to_blank_ternary()

        self.main_splitter = CustomSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.dynamic_content_area)
        self.main_splitter.addWidget(self.plot_scroll_area)

        # Main Layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addWidget(self.tab_view, 1)
        # self.main_layout.addWidget(self.dynamic_content_area, 3)
        # self.main_layout.addWidget(self.plot_scroll_area, 3)
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

        QApplication.instance().paletteChanged.connect(self.on_palette_changed)

    def setupFonts(self):
        font_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'assets',
            'fonts',
            'OpenSans-Regular.ttf')
        QFontDatabase.addApplicationFont(font_path)

    @Slot()
    def on_palette_changed(self):
        """
        Slot that is called when the application's palette changes.
        """
        QTimer.singleShot(750, lambda: self.update_title_view("quick ternaries"))

    def switch_to_start_setup_view(self):
        self.dynamic_content_area.setCurrentWidget(self.ternary_start_setup_view)
    
    def switch_to_trace_view(self):
        self.dynamic_content_area.setCurrentWidget(self.ternary_trace_editor_view)

    def switch_to_standard_trace_view(self):
        self.switch_to_trace_view()
        self.ternary_trace_editor_view.switch_to_standard_view()
    
    def switch_to_bootstrap_trace_view(self):
        self.switch_to_trace_view()
        self.ternary_trace_editor_view.switch_to_bootstrap_view()

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

    def switch_to_blank_ternary(self):
        url = QUrl.fromLocalFile(self.BLANK_TERNARY_PATH)
        self.plot_view.setUrl(url)

    def switch_to_blank_cartesian(self):
        url = QUrl.fromLocalFile(self.BLANK_CARTESIAN_PATH)
        self.plot_view.setUrl(url)

    def show_bootstrap_tutorial_gif(self):
        tutorial_gif = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'resources', 
            'bootstrap-tutorial.gif')
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
        font_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'assets',
            'fonts',
            'Motter_Tektura_Normal.ttf')
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

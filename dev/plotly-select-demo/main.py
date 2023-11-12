import sys
import pandas as pd
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog, QColorDialog
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QObject, Slot
from plotly_interface import PlotlyInterface
from plotly.offline import plot
from plotly.subplots import make_subplots
import plotly.graph_objects as go

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Layout and central widget
        centralWidget = QWidget(self)
        self.setCentralWidget(centralWidget)
        layout = QVBoxLayout(centralWidget)

        # Button to load data
        self.loadButton = QPushButton("Load Data", self)
        self.loadButton.clicked.connect(self.loadData)

        # Button to change color
        self.colorButton = QPushButton("Change Color", self)
        self.colorButton.clicked.connect(self.changeColor)

        # Plotly Ternary Plot (WebEngineView)
        self.webEngineView = QWebEngineView(self)
        self.setupWebChannel()

        # Add widgets to layout
        layout.addWidget(self.loadButton)
        layout.addWidget(self.colorButton)
        layout.addWidget(self.webEngineView)

        # Initialize data
        self.data = pd.DataFrame(columns=['A', 'B', 'C', 'color'])
        self.data['color'] = 'red'  # Default color

        # Initial plot
        self.plotTernary()

    def setupWebChannel(self):
        self.plotlyInterface = PlotlyInterface(self)
        channel = QWebChannel(self.webEngineView.page())
        channel.registerObject("plotlyInterface", self.plotlyInterface)
        self.webEngineView.page().setWebChannel(channel)

    @Slot()
    def loadData(self):
        file_name = QFileDialog.getOpenFileName(self, "Open Data File", "", "CSV Files (*.csv)")
        if file_name[0]:
            self.data = pd.read_csv(file_name[0])
            self.data['color'] = 'red'  # Reset color on new data load
            self.plotTernary()

    @Slot()
    def changeColor(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.plotlyInterface.selectedColor = color.name()
            # Apply color change to currently selected indices
            self.plotlyInterface.applyColorChange()

    def plotTernary(self):
        fig = make_subplots(rows=1, cols=1, specs=[[{'type': 'ternary'}]])
        fig.add_trace(go.Scatterternary(a=self.data['A'], b=self.data['B'], c=self.data['C'],
                                        mode='markers', marker={'color': self.data['color']}))

        html_str = plot(fig, output_type='div', include_plotlyjs='cdn')
        js_code = """
            <script type="text/javascript" src="qrc:///qtwebchannel/qwebchannel.js"></script>
            <script type="text/javascript">
                document.addEventListener("DOMContentLoaded", function() {
                    new QWebChannel(qt.webChannelTransport, function (channel) {
                        window.plotlyInterface = channel.objects.plotlyInterface;
                        var plotElement = document.getElementsByClassName('plotly-graph-div')[0];
                        plotElement.on('plotly_selected', function(eventData) {
                            if (eventData) {
                                var indices = eventData.points.map(function(pt) { return pt.pointIndex; });
                                window.plotlyInterface.receiveSelectedIndices(indices);
                            }
                        });
                    });
                });
            </script>
        """

        complete_html = html_str + js_code
        self.webEngineView.setHtml(complete_html)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


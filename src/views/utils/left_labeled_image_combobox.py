import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import get_colorscale

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox, 
    QSizePolicy
)

from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

class LeftLabeledImageComboBox(QWidget):
    """A labeled ComboBox megawidget, for combo boxes with QLabels to their left"""
    
    valueChanged = Signal(str)

    def __init__(self, label: str = '', parent: QWidget | None = None):
        super().__init__(parent)
        self.layout = QHBoxLayout()

        self.label = QLabel(label)
        self.combobox = QComboBox()
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.combobox)
        self.setLayout(self.layout)

        # Connect internal QComboBox signal to the new signal
        self.combobox.currentIndexChanged.connect(self.emit_value_changed)
        
    def addItems(self, items: list[str]):
        if items is not None:
            self.combobox.blockSignals(True)
            self.combobox.addItems(items)
            self.combobox.blockSignals(False)

    def addIcons(self, icons: list[QIcon], labels: list[str], icon_size: QSize):
        if icons is not None:
            self.combobox.blockSignals(True)
            for icon, label in zip(icons, labels):
                self.combobox.addItem(icon, label, label)
            self.combobox.blockSignals(False)
            self.combobox.setIconSize(icon_size)

    def addPlotlyIcons(self, symbols: list[str]):
        icons = [self.create_plotly_marker_icon(symbol) for symbol in symbols]
        self.addIcons(icons, symbols, QSize(14, 14))
    
    def addColorscaleIcons(self, colorscales: list[str]):
        icons = [self.create_colorscale_icon(colorscale) for colorscale in colorscales]
        self.addIcons(icons, colorscales, QSize(100, 20))

    def currentText(self):
        return self.combobox.currentText()

    def setCurrentText(self, text: str, block: bool=True):
        index = self.combobox.findText(text)
        if index >= 0:
            if block:
                self.combobox.blockSignals(True)
                self.combobox.setCurrentIndex(index)
                self.combobox.blockSignals(False)
            else:
                self.combobox.setCurrentIndex(index)
        else:
            self.combobox.setCurrentIndex(0)

    def clear(self):
        self.combobox.blockSignals(True)
        self.combobox.clear()
        self.combobox.blockSignals(False)

    def emit_value_changed(self, index):
        text = self.combobox.itemText(index)
        self.valueChanged.emit(text)

    def create_plotly_marker_icon(self, shape, size=32):
        # Create a subplot with a single cell
        fig = make_subplots(rows=1, cols=1)
        
        # Add a scatter trace with the desired marker
        fig.add_trace(go.Scatter(
            x=[0], y=[0],
            mode='markers',
            marker=dict(symbol=shape, size=size*0.8, color='black')
        ))
        
        # Update the layout to remove axes and set a fixed range
        fig.update_layout(
            width=size, height=size,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False, range=[-1, 1]),
            yaxis=dict(visible=False, range=[-1, 1]),
            showlegend=False
        )
        
        # Convert to image
        img_bytes = fig.to_image(format="png")
        
        # Create QIcon
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)
        return QIcon(pixmap)

    def create_colorscale_icon(self, colorscale_name, width=100, height=20):
        colorscale = get_colorscale(colorscale_name)
        
        # Create a subplot with a single cell
        fig = make_subplots(rows=1, cols=1)
        
        # Create a heatmap trace
        heatmap_data = np.array([[i for i in range(100)]])
        fig.add_trace(go.Heatmap(z=heatmap_data, colorscale=colorscale, showscale=False))
        
        # Update the layout
        fig.update_layout(
            width=width, height=height,
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False
        )
        
        # Convert to image
        img_bytes = fig.to_image(format="png")
        
        # Create QIcon
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)
        return QIcon(pixmap)
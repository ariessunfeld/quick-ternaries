from PySide6.QtCore import Qt

from PySide6.QtWidgets import (
    QScrollArea,
    QLabel,
    QWidget,
    QHBoxLayout,
    QSizePolicy,
    QFrame,
)

class HorizontalScrollArea(QScrollArea):
    """
    A QScrollArea that translates vertical wheel events into horizontal scrolling.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)

    def wheelEvent(self, event):
        # Translate vertical scrolling into horizontal scrolling
        delta = event.angleDelta().y()
        new_value = self.horizontalScrollBar().value() - delta
        self.horizontalScrollBar().setValue(new_value)
        event.accept()


class ScrollableLabel(QWidget):
    """
    A widget containing a horizontally scrollable QLabel that looks like a line edit.
    We set a smaller font, smaller padding, and fix/limit the height for a 'normal' look.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # A horizontal layout for the scroll area
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = HorizontalScrollArea()
        # Expand horizontally, but do not expand vertically
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.scroll_area)

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setWordWrap(False)  # single-line behavior

        # Style to resemble a line edit, but with smaller font & padding
        self.label.setStyleSheet("""
            QLabel {
                background-color: rgba(240, 240, 240, 0.5);
                border: 1px solid #c0c0c0;
                border-radius: 2px;
                padding: 2px;            /* smaller padding */
                font-family: system-ui;
                font-size: 12px;         /* smaller font */
            }
        """)
        # Expand horizontally, fixed vertically
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Option 1: Fix the overall widget height to about 24 px
        # (Comment out if you prefer a max height or no limit.)
        # self.setFixedHeight(24)

        # Option 2: Alternatively, set a maximum height:
        self.setMaximumHeight(24)

        self.scroll_area.setWidget(self.label)

    def setText(self, text: str):
        self.label.setText(text)

    def text(self) -> str:
        return self.label.text()
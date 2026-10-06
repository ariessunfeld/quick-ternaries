"""Visible consent and lifecycle controls for one desktop connection."""

import json

from PySide6.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from quick_ternaries.views.accessibility import describe_control
from .server import DesktopApi
from .snapshot import WorkspaceReader


class AgentConnectionDialog(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Agent connection")
        self.setMinimumWidth(480)
        self.api = DesktopApi(lambda instance: WorkspaceReader(window, instance), self)
        self._copied_details = None
        self._read_count = 0
        layout = QVBoxLayout(self)
        explanation = QLabel(
            "Allow a local agent to read this window's plot settings, trace and filter "
            "details, and loaded dataset names and column schemas. Data rows are excluded. "
            "Editing and export are not available yet.\n\n"
            "Share connection details only with an agent you choose. Access lasts until "
            "you disconnect or close this window."
        )
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.status = QLabel("Disconnected")
        layout.addWidget(self.status)
        self.address = QLineEdit()
        self.address.setReadOnly(True)
        describe_control(self.address, "agent.connection_address", "Local connection address")
        layout.addWidget(self.address)
        self.toggle = QPushButton("Enable read-only connection")
        describe_control(self.toggle, "agent.connection_toggle", "Enable read-only connection")
        self.toggle.clicked.connect(self.toggle_connection)
        layout.addWidget(self.toggle)
        self.copy = QPushButton("Copy connection details")
        describe_control(self.copy, "agent.connection_copy", "Copy connection details",
                         "Copies the address, instance ID, and secret token for your chosen agent.")
        self.copy.setEnabled(False)
        self.copy.clicked.connect(self.copy_details)
        layout.addWidget(self.copy)
        self.activity = QLabel("No reads in this connection")
        layout.addWidget(self.activity)
        self.api.read_completed.connect(self._read_completed)
        QApplication.instance().aboutToQuit.connect(self.stop)

    def toggle_connection(self):
        if self.api.running:
            self.stop()
            return
        try:
            self.api.start()
        except OSError:
            self.status.setText("Could not start the local connection. Try again.")
            return
        self._read_count = 0
        self.activity.setText("No reads in this connection")
        self.status.setText("Connected · Read only")
        self.address.setText(self.api.connection_details()["url"])
        self.toggle.setText("Disconnect agent access")
        self.toggle.setAccessibleName(self.toggle.text())
        self.copy.setEnabled(True)
        self.window.agentButton.setText("Agent API: Read only")
        self.window.agentButton.setAccessibleName(self.window.agentButton.text())

    def copy_details(self):
        self._copied_details = json.dumps(self.api.connection_details())
        QApplication.clipboard().setText(self._copied_details)

    def _read_completed(self, endpoint):
        self._read_count += 1
        label = "workspace" if endpoint == "/v1/workspace" else "capabilities"
        self.activity.setText(f"{self._read_count} reads · Last read: {label}")

    def stop(self):
        self.api.stop()
        clipboard = QApplication.clipboard()
        if self._copied_details and clipboard.text() == self._copied_details:
            clipboard.clear()
        self._copied_details = None
        self.status.setText("Disconnected")
        self.address.clear()
        self.copy.setEnabled(False)
        self.toggle.setText("Enable read-only connection")
        self.toggle.setAccessibleName(self.toggle.text())
        self.window.agentButton.setText("Agent API: Off")
        self.window.agentButton.setAccessibleName(self.window.agentButton.text())

    def closeEvent(self, event):
        # Closing this settings panel keeps the explicitly enabled connection;
        # the main window always displays its state and closes it on exit.
        event.accept()

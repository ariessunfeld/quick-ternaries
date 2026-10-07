"""Visible consent and lifecycle controls for one desktop connection."""

import json

from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout

from quick_ternaries.views.accessibility import describe_control
from .server import DesktopApi
from .snapshot import WorkspaceReader


class AgentConnectionDialog(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Agent connection")
        self.setMinimumWidth(480)
        self.api = DesktopApi(lambda instance: WorkspaceReader(window, instance), self,
                              workspace_session=getattr(window, "workspace_session", None),
                              workspace_controller=getattr(window, "workspace_commands", None))
        self._copied_details = None
        self._read_count = 0
        layout = QVBoxLayout(self)
        explanation = QLabel(
            "Allow a local agent to read this window's plot settings, trace styles, heatmaps, "
            "filters, and loaded dataset names and column schemas. Data rows are excluded. "
            "Optional editing lets your agent change plot settings, styles, filters and traces, and render the plot. Workspace edits can be undone from the Edit menu. File import and export remain under your control.\n\n"
            "Share connection details with your chosen agent once. Its persistent client "
            "can keep reading after you copy something else. Access lasts until "
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
        self.allow_edit = QCheckBox("Allow workspace editing")
        describe_control(self.allow_edit, "agent.allow_workspace_edits", "Allow workspace editing")
        self.allow_edit.setEnabled(False)
        self.allow_edit.toggled.connect(self._set_edit_permission)
        layout.addWidget(self.allow_edit)
        self.api.edit_completed.connect(self._edit_completed)
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
        self.allow_edit.setEnabled(self.api.workspace_session is not None)
        self.window.agentButton.setText("Agent API: Read only")
        self.window.agentButton.setAccessibleName(self.window.agentButton.text())

    def _set_edit_permission(self, enabled):
        self.api.edit_enabled = bool(enabled and self.api.running and self.api.workspace_session is not None)
        if not self.api.edit_enabled:
            self.window.workspace_commands.render.cancel_pending()
        if self.api.running:
            mode = "Editing" if self.api.edit_enabled else "Read only"
            self.status.setText(f"Connected · {mode}")
            self.window.agentButton.setText(f"Agent API: {mode}")
            self.window.agentButton.setAccessibleName(self.window.agentButton.text())

    def _edit_completed(self, label):
        self.activity.setText(f"Last agent action: {label}")

    def copy_details(self):
        self._copied_details = json.dumps(self.api.connection_details())
        QApplication.clipboard().setText(self._copied_details)

    def _read_completed(self, endpoint):
        self._read_count += 1
        label = endpoint.removeprefix("/v1/").split("/")[0]
        self.activity.setText(f"{self._read_count} reads · Last read: {label}")

    def stop(self):
        self.api.stop()
        self.allow_edit.setChecked(False)
        self.allow_edit.setEnabled(False)
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

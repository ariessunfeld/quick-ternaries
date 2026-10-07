"""Application settings, separate from the plotting workspace."""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QPushButton, QVBoxLayout

from quick_ternaries.views.accessibility import describe_control


class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(360)
        describe_control(self, "settings.window", "Settings")
        layout = QVBoxLayout(self)
        explanation = QLabel("Connect a local agent to this workspace and manage its access.")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.agentButton = QPushButton("Agent API: Off")
        describe_control(self.agentButton, "settings.agent_connection", self.agentButton.text())
        layout.addWidget(self.agentButton)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)

    def set_agent_state(self, state):
        self.agentButton.setText(f"Agent API: {state}")
        self.agentButton.setAccessibleName(self.agentButton.text())

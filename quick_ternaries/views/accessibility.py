"""Shared accessibility metadata for native and composite form controls.

Identifiers describe controls in the current editor, not document objects.
They stay stable across view rebuilds; workspace/trace identity belongs in the
application model and must never be inferred from an accessibility identifier.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QComboBox, QWidget


def describe_control(widget: QWidget, identifier: str, name: str,
                     description: str = "") -> None:
    """Give a control a stable automation ID and a human-readable name."""
    widget.setObjectName(identifier)
    widget.setAccessibleIdentifier(identifier)
    widget.setAccessibleName(name.rstrip(":"))
    # Qt's combo-box interface can expose currentText as its accessible Name.
    # Preserve the field's purpose in Description as well as the widget name.
    if description or isinstance(widget, QComboBox):
        widget.setAccessibleDescription(description or name.rstrip(":"))


def describe_field(widget: QWidget, identifier: str, label: str) -> None:
    """Label generated fields, including the interactive children of composites.

    Custom controls opt in with ``set_accessible_field`` so this helper does not
    guess at Qt implementation children or depend on their traversal order.
    """
    name = label.rstrip(":")
    describe_control(widget, identifier, name)
    configure = getattr(widget, "set_accessible_field", None)
    if configure is not None:
        configure(identifier, name)


def focus_through(widget: QWidget, control: QWidget) -> None:
    """Let a form label/buddy focus the meaningful child of a composite."""
    widget.setFocusProxy(control)
    widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


def add_focus_shortcut(owner: QWidget, control: QWidget, keys: str) -> QShortcut:
    """Provide a direct focus path independent of platform Tab preferences."""
    sequence = QKeySequence(keys)
    shortcut = QShortcut(sequence, owner)
    shortcut.activated.connect(lambda: control.setFocus(Qt.FocusReason.ShortcutFocusReason))
    hint = f"Press {sequence.toString(QKeySequence.SequenceFormat.NativeText)} to focus."
    description = control.accessibleDescription().rstrip(".")
    control.setAccessibleDescription(f"{description}. {hint}" if description else hint)
    control.setToolTip(hint)
    return shortcut

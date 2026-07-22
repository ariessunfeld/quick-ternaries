from unittest.mock import MagicMock

from quick_ternaries.views.trace_editor_view import TraceEditorView


def test_heatmap_bound_spinboxes_accept_negative_values():
    for field_name in ("heatmap_min", "heatmap_max"):
        spinbox = MagicMock()

        TraceEditorView._configure_double_spinbox(field_name, spinbox)

        spinbox.setRange.assert_called_once_with(-1e10, 1e10)

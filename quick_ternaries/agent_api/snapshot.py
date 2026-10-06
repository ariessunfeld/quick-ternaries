"""Bounded public projections, deliberately independent of workspace persistence."""

import hashlib
import json
import math
from pathlib import Path
from uuid import UUID, uuid5

from PySide6.QtCore import QThread, Qt

from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.trace_editor_model import TraceEditorModel

MAX_TRACES = 200
MAX_DATASETS = 64
MAX_COLUMNS = 128
MAX_FILTERS = 50
MAX_TEXT = 512
MAX_VALUES = 8192
MAX_TOTAL_TEXT = 64 * 1024


class WorkspaceReader:
    """Read only on the GUI thread; never load files, render, or commit editors.

    IDs are scoped to the connection. snapshot_id fingerprints just this public
    projection: it is NOT a document revision or a future write precondition.
    """

    def __init__(self, window, instance_id):
        self.window = window
        self.namespace = UUID(instance_id)

    def snapshot(self):
        window = self.window
        if QThread.currentThread() != window.thread():
            raise RuntimeError("Workspace snapshots must run on the GUI thread")
        self.truncated = False
        self.values_left = MAX_VALUES
        self.text_left = MAX_TOTAL_TEXT
        library = window.setupMenuModel.data_library

        def metadata_key(metadata):
            return json.dumps([metadata.file_path, metadata.header_row, metadata.sheet])

        def dataset_id(metadata):
            return str(uuid5(self.namespace, metadata_key(metadata)))

        datasets = []
        known_datasets = {}
        for metadata in self.limited(library.loaded_files, MAX_DATASETS):
            key = metadata_key(metadata)
            if key in known_datasets:
                continue
            uid = dataset_id(metadata)
            known_datasets[key] = uid
            # This cache-only accessor cannot reload a missing file or modify metadata.
            df = library.dataframe_manager.get_dataframe(metadata.df_id)
            columns = []
            if df is not None:
                for index in range(min(len(df.columns), MAX_COLUMNS)):
                    columns.append({"name": self.value(df.columns[index]),
                                    "dtype": str(df.iloc[:, index].dtype)})
                self.truncated |= len(df.columns) > MAX_COLUMNS
            datasets.append({
                "id": uid, "name": self.value(Path(metadata.file_path).name),
                "header_row": metadata.header_row, "sheet": self.value(metadata.sheet),
                "loaded": df is not None, "row_count": len(df) if df is not None else None,
                "column_count": len(df.columns) if df is not None else None,
                "columns": columns,
            })

        traces = []
        trace_count = 0
        panel = window.tabPanel
        for index in range(panel.listWidget.count()):
            uid = panel.listWidget.item(index).data(Qt.ItemDataRole.UserRole)
            model = panel.id_to_widget.get(uid)
            if not isinstance(model, TraceEditorModel):
                continue
            trace_count += 1
            if len(traces) >= MAX_TRACES:
                self.truncated = True
                continue
            metadata = model.datafile
            if isinstance(metadata, str):
                metadata = DataFileMetadata.from_display_string(metadata)
            data_id = (known_datasets.get(metadata_key(metadata))
                       if isinstance(metadata, DataFileMetadata) else None)
            traces.append({
                "id": str(uid), "name": self.value(model.trace_name),
                "dataset_id": data_id, "visible": not model.hide_on,
                "color": self.value(model.trace_color), "marker": self.value(model.point_shape),
                "marker_size": self.value(model.point_size), "is_contour": model.is_contour,
                "filters_enabled": model.filters_on, "filter_count": len(model.filters),
                "filters": [
                    {"name": self.value(f.filter_name), "column": self.value(f.filter_column),
                     "operation": self.value(f.filter_operation),
                     "value1": self.value(f.filter_value1), "value2": self.value(f.filter_value2)}
                    for f in self.limited(model.filters, MAX_FILTERS)
                ],
            })
        axes = window.setupMenuModel.axis_members
        result = {
            "plot_type": window.plotTypeSelector.currentText().lower(),
            "title": self.value(window.setupMenuModel.plot_labels.title),
            "axes": {name: self.value(getattr(axes, name)) for name in (
                "x_axis", "y_axis", "top_axis", "left_axis", "right_axis",
                "categorical_column", "numerical_columns", "hover_data")},
            "datasets": datasets, "dataset_count": len(library.loaded_files),
            "traces": traces, "trace_count": trace_count, "truncated": self.truncated,
        }
        digest = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
        return {"snapshot_id": digest, **result}

    def limited(self, values, maximum):
        self.truncated |= len(values) > maximum
        return values[:maximum]

    def value(self, value):
        if self.values_left <= 0:
            self.truncated = True
            return None
        self.values_left -= 1
        if value is None or isinstance(value, (bool, int)):
            return value
        if isinstance(value, float):
            return value if math.isfinite(value) else None
        if isinstance(value, (list, tuple)):
            return [self.value(v) for v in self.limited(value, min(MAX_COLUMNS, self.values_left))]
        text = str(value)
        length = min(MAX_TEXT, self.text_left)
        self.truncated |= len(text) > length
        text = text[:length]
        self.text_left -= len(text)
        return text

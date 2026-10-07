"""Bounded public projections, deliberately independent of workspace persistence."""

import hashlib
import json
import math
from pathlib import Path
from uuid import UUID, uuid5

from PySide6.QtCore import QThread, Qt

from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from .contract import ApiError, TRACE_SECTIONS, coverage

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
        self.prepare()
        library = window.setupMenuModel.data_library

        datasets = []
        known_datasets = set()
        for metadata in self.limited(library.loaded_files, MAX_DATASETS):
            key = self.metadata_key(metadata)
            if key in known_datasets:
                continue
            known_datasets.add(key)
            dataset = self.dataset_value(metadata, 0, MAX_COLUMNS)
            self.truncated |= dataset["next_offset"] is not None
            datasets.append(dataset)

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
            traces.append(self.trace_value(uid, model))
        axes = window.setupMenuModel.axis_members
        result = {
            "plot_type": window.plotTypeSelector.currentText().lower(),
            "title": self.value(window.setupMenuModel.plot_labels.title),
            "axes": {name: self.value(getattr(axes, name)) for name in (
                "x_axis", "y_axis", "top_axis", "left_axis", "right_axis",
                "categorical_column", "numerical_columns", "hover_data")},
            "datasets": datasets, "dataset_count": len(library.loaded_files),
            "traces": traces, "trace_count": trace_count, "truncated": self.truncated,
            "selected_trace_id": self.selected_trace_id(),
            "coverage": coverage(["plot_type", "title", "axes", "trace_sections", "dataset_schema"]),
        }
        digest = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
        return {"snapshot_id": digest, **result}

    @property
    def document_epoch(self):
        return getattr(self.window, "_agent_document_epoch", 0)

    def prepare(self):
        window = self.window
        if QThread.currentThread() != window.thread():
            raise RuntimeError("Workspace snapshots must run on the GUI thread")
        if getattr(window, "_agent_loading_workspace", False):
            raise ApiError("workspace_busy", "Workspace loading is in progress. Retry after it finishes.", 503)
        self.truncated = False
        self.values_left = MAX_VALUES
        self.text_left = MAX_TOTAL_TEXT

    @staticmethod
    def metadata_key(metadata):
        return json.dumps([metadata.file_path, metadata.header_row, metadata.sheet])

    def dataset_id(self, metadata):
        return str(uuid5(self.namespace, self.metadata_key(metadata)))

    def selected_trace_id(self):
        panel = self.window.tabPanel
        item = panel.listWidget.currentItem()
        uid = item.data(Qt.ItemDataRole.UserRole) if item else None
        return str(uid) if isinstance(panel.id_to_widget.get(uid), TraceEditorModel) else None

    def trace_identity(self, uid, model):
        metadata = model.datafile
        if isinstance(metadata, str):
            metadata = DataFileMetadata.from_display_string(metadata)
        data_id = self.dataset_id(metadata) if isinstance(metadata, DataFileMetadata) and metadata.file_path else None
        return {"id": str(uid), "name": self.value(model.trace_name),
                "dataset_id": data_id, "visible": not model.hide_on, "is_contour": model.is_contour}

    def filter_page(self, model, offset, limit):
        values = model.filters[offset:offset + limit]
        return {"enabled": model.filters_on, "total": len(model.filters), "offset": offset,
                "next_offset": offset + limit if offset + limit < len(model.filters) else None,
                "items": [{"name": self.value(f.filter_name), "column": self.value(f.filter_column),
                           "operation": self.value(f.filter_operation),
                           "value1": self.value(f.filter_value1), "value2": self.value(f.filter_value2)}
                          for f in values]}

    def trace_value(self, uid, model):
        filters = self.filter_page(model, 0, MAX_FILTERS)
        self.truncated |= filters["next_offset"] is not None
        return {
            **self.trace_identity(uid, model),
            "color": self.value(model.trace_color), "marker": self.value(model.point_shape),
            "marker_size": self.value(model.point_size), "filters_enabled": model.filters_on,
            "filter_count": len(model.filters), "filters": filters["items"],
            **{section: self.trace_section(model, section) for section in TRACE_SECTIONS},
        }

    def trace_section(self, model, section):
        return {name: self.value(getattr(model, name)) for name in TRACE_SECTIONS[section]}

    def trace(self, uid, sections, offset=0, limit=50):
        self.prepare()
        model = self.window.tabPanel.id_to_widget.get(uid)
        if not isinstance(model, TraceEditorModel):
            raise ApiError("trace_not_found", "This trace is no longer available. Refresh the overview.", 404)
        result = self.trace_identity(uid, model)
        for section in sections:
            if section == "filters":
                result[section] = self.filter_page(model, offset, limit)
            elif section != "identity":
                result[section] = self.trace_section(model, section)
        return {"trace": result, "truncated": self.truncated,
                "coverage": coverage(["identity", *sections])}

    def dataset_value(self, metadata, offset, limit):
        # Cache-only access: never reload a file to answer an agent.
        df = self.window.setupMenuModel.data_library.dataframe_manager.get_dataframe(metadata.df_id)
        columns = []
        if df is not None:
            for index in range(offset, min(offset + limit, len(df.columns))):
                columns.append({"index": index, "name": self.value(df.columns[index]),
                                "dtype": str(df.iloc[:, index].dtype)})
        total = len(df.columns) if df is not None else None
        return {"id": self.dataset_id(metadata), "name": self.value(Path(metadata.file_path).name),
                "header_row": metadata.header_row, "sheet": self.value(metadata.sheet),
                "loaded": df is not None, "row_count": len(df) if df is not None else None,
                "column_count": total, "columns": columns, "offset": offset,
                "next_offset": offset + limit if total is not None and offset + limit < total else None}

    def dataset(self, uid, offset=0, limit=50):
        self.prepare()
        for metadata in self.window.setupMenuModel.data_library.loaded_files:
            if self.dataset_id(metadata) == uid:
                return {"dataset": self.dataset_value(metadata, offset, limit),
                        "truncated": self.truncated, "coverage": coverage(["dataset_metadata", "column_page"])}
        raise ApiError("dataset_not_found", "This dataset is no longer available. Refresh the overview.", 404)

    def catalog(self, kind, offset=0, limit=20):
        self.prepare()
        items = []
        if kind == "traces":
            panel = self.window.tabPanel
            total = 0
            for index in range(panel.listWidget.count()):
                uid = panel.listWidget.item(index).data(Qt.ItemDataRole.UserRole)
                model = panel.id_to_widget.get(uid)
                if isinstance(model, TraceEditorModel):
                    if offset <= total < offset + limit:
                        items.append(self.trace_identity(uid, model))
                    total += 1
        else:
            library = self.window.setupMenuModel.data_library
            total = len(library.loaded_files)
            for metadata in library.loaded_files[offset:offset + limit]:
                item = self.dataset_value(metadata, 0, 0)
                items.append({key: value for key, value in item.items()
                              if key not in ("columns", "offset", "next_offset")})
        return {kind: items, "total": total, "offset": offset,
                "next_offset": offset + limit if offset + limit < total else None,
                "truncated": self.truncated, "coverage": coverage([kind + "_summary_page"])}

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
            self.truncated |= not math.isfinite(value)
            return value if math.isfinite(value) else None
        if isinstance(value, (list, tuple)):
            return [self.value(v) for v in self.limited(value, min(MAX_COLUMNS, self.values_left))]
        text = str(value)
        length = min(MAX_TEXT, self.text_left)
        self.truncated |= len(text) > length
        text = text[:length]
        self.text_left -= len(text)
        return text

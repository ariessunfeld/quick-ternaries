from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pandas as pd

from quick_ternaries.controllers.trace_editor_controller import TraceEditorController
from quick_ternaries.models.data_file_metadata_model import DataFileMetadata
from quick_ternaries.models.trace_editor_model import TraceEditorModel


def test_heatmap_bounds_use_negative_column_range():
    model = TraceEditorModel(
        datafile=DataFileMetadata(file_path="patrick.xlsx"),
        heatmap_column="elev",
    )
    view = SimpleNamespace(widgets={})
    data_library = MagicMock()
    data_library.dataframe_manager.get_dataframe_by_metadata.return_value = (
        pd.DataFrame(
            {
                "elev": [-3657.18, -3610.2, -3595.06, np.nan, np.inf],
            }
        )
    )

    controller = TraceEditorController(model, view, data_library)
    controller._update_heatmap_min_max_for_column("elev")

    assert model.heatmap_min == -3657.18
    assert model.heatmap_max == -3595.06

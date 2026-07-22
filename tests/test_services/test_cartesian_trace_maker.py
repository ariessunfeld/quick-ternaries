import pandas as pd
import pytest

from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.services.cartesian_trace_maker import CartesianTraceMaker


def test_heatmap_preserves_negative_color_values_and_bounds():
    data = pd.DataFrame({"elev": [-3657.18, -3610.2, -3595.06]})
    model = TraceEditorModel(
        heatmap_column="elev",
        heatmap_min=-3657.18,
        heatmap_max=-3595.06,
    )

    marker, plotted_data = CartesianTraceMaker()._update_marker_with_heatmap(
        {}, model, data.copy(), "negative"
    )

    assert marker["cmin"] == -3657.18
    assert marker["cmax"] == -3595.06
    assert marker["color"].tolist() == data["elev"].tolist()
    assert plotted_data["__elev_heatmap_negative"].tolist() == data["elev"].tolist()


def test_sizemap_normalizes_negative_data_to_positive_marker_sizes():
    data = pd.DataFrame({"elev": [-3657.18, -3610.2, -3595.06, None]})
    model = TraceEditorModel(
        sizemap_column="elev",
        sizemap_min=2.0,
        sizemap_max=6.0,
    )

    marker, _ = CartesianTraceMaker()._update_marker_with_sizemap(
        {}, model, data.copy(), "negative"
    )

    assert min(marker["size"]) == pytest.approx(2.0)
    assert max(marker["size"]) == pytest.approx(6.0)
    assert not marker["size"].isna().any()
    assert list(marker["size"].iloc[:3]) == sorted(marker["size"].iloc[:3])

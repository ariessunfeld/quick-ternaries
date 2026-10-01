"""Regression coverage for filters that remove every row from a trace."""

from itertools import permutations
from unittest.mock import patch

import pandas as pd
import pytest

from quick_ternaries.models.filter_model import FilterModel
from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.services.cartesian_trace_maker import CartesianTraceMaker
from quick_ternaries.services.ternary_trace_maker import (
    DensityContourMaker,
    TernaryTraceMaker,
)


@pytest.fixture(params=[TernaryTraceMaker, CartesianTraceMaker, DensityContourMaker])
def trace_maker(request):
    return request.param()


@pytest.mark.parametrize(
    "operation,value1,value2",
    [
        ("<", "4711", ""),
        (">", "4743", ""),
        ("<=", "4710", ""),
        (">=", "4744", ""),
        ("==", "4720", ""),
        ("is", "4720", ""),
        ("is not", "4712", ""),
        ("is one of", ["4720", "4730"], ""),
        ("is not one of", ["4712"], ""),
        ("a < x < b", "4720", "4743"),
        ("a <= x < b", "4720", "4743"),
        ("a < x <= b", "4720", "4743"),
        ("a <= x <= b", "4720", "4743"),
    ],
)
def test_zero_matches_stay_empty(trace_maker, operation, value1, value2):
    data = pd.DataFrame({"Sol": [4712, 4712]}, index=[4, 9])
    original = data.copy(deep=True)
    trace = TraceEditorModel(
        filters_on=True,
        filters=[FilterModel(
            filter_column="Sol",
            filter_operation=operation,
            filter_value1=value1,
            filter_value2=value2,
        )],
    )

    result = trace_maker._apply_filters(data, trace)

    pd.testing.assert_frame_equal(result, data.iloc[:0])
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize("filter_order", list(permutations(range(3))))
def test_category_distance_and_sol_range_intersect(trace_maker, filter_order):
    # Each condition has matches, but no nodule meets all three conditions.
    data = pd.DataFrame({
        "Sub-Category": ["Nodule", "Nodule ", "Nodule", "Vein"],
        "Distance (m)": [3.0, 3.0, 5.0, 3.0],
        "Sol": [4706, 4750, 4720, 4720],
    })
    filters = [
        FilterModel(filter_column="Distance (m)", filter_operation="<", filter_value1="4"),
        FilterModel(
            filter_column="Sub-Category",
            filter_operation="is one of",
            filter_value1=["Nodule", "Nodule "],
        ),
        FilterModel(
            filter_column="Sol", filter_operation="a < x < b",
            filter_value1="4711", filter_value2="4743",
        ),
    ]
    trace = TraceEditorModel(filters_on=True, filters=[filters[i] for i in filter_order])

    assert trace_maker._apply_filters(data, trace).empty


def test_separate_sol_bounds_do_not_restore_rejected_rows(trace_maker):
    data = pd.DataFrame({"Sol": [4706, 4750, 4831]})
    trace = TraceEditorModel(filters_on=True, filters=[
        FilterModel(filter_column="Sol", filter_operation=">", filter_value1="4711"),
        FilterModel(filter_column="Sol", filter_operation="<", filter_value1="4743"),
        FilterModel(filter_column="Sol", filter_operation=">", filter_value1="0"),
    ])

    assert trace_maker._apply_filters(data, trace).empty


@pytest.mark.parametrize(
    "operation,expected_indices",
    [
        ("a < x < b", [1]),
        ("a <= x < b", [0, 1]),
        ("a < x <= b", [1, 2]),
        ("a <= x <= b", [0, 1, 2]),
    ],
)
def test_range_boundaries_keep_matching_rows(trace_maker, operation, expected_indices):
    data = pd.DataFrame({"Sol": [4711, 4720, 4743, 4750]})
    trace = TraceEditorModel(filters_on=True, filters=[FilterModel(
        filter_column="Sol", filter_operation=operation,
        filter_value1="4711", filter_value2="4743",
    )])

    pd.testing.assert_frame_equal(
        trace_maker._apply_filters(data, trace), data.loc[expected_indices]
    )


@pytest.mark.parametrize("filters_on", [False, True])
def test_disabled_or_absent_filters_preserve_data(trace_maker, filters_on):
    data = pd.DataFrame({"Sol": [4706, 4750]})
    trace = TraceEditorModel(filters_on=filters_on, filters=[] if filters_on else [
        FilterModel(filter_column="Sol", filter_operation="<", filter_value1="0"),
    ])

    pd.testing.assert_frame_equal(trace_maker._apply_filters(data, trace), data)


@pytest.mark.parametrize("maker_class,coordinates", [
    (TernaryTraceMaker, ["a", "b", "c"]),
    (CartesianTraceMaker, ["x", "y"]),
])
@pytest.mark.parametrize("heatmap_on,sizemap_on", [
    (False, False), (True, False), (False, True), (True, True),
])
def test_empty_filter_result_plots_no_points(
    maker_class, coordinates, heatmap_on, sizemap_on
):
    data = pd.DataFrame({"Sol": [4750, 4831], "A": [1.0, 2.0], "B": [3.0, 4.0]})
    setup = SetupMenuModel()
    setup.axis_members.top_axis = ["A"]
    setup.axis_members.left_axis = ["B"]
    setup.axis_members.right_axis = ["A", "B"]
    setup.axis_members.x_axis = ["A"]
    setup.axis_members.y_axis = ["B"]
    setup.axis_members.hover_data = ["Sol"]
    trace = TraceEditorModel(
        heatmap_on=heatmap_on, heatmap_column="Sol",
        sizemap_on=sizemap_on, sizemap_column="Sol",
        filters_on=True,
        filters=[FilterModel(filter_column="Sol", filter_operation="<", filter_value1="4743")],
    )
    with patch.object(
        setup.data_library.dataframe_manager, "get_dataframe_by_metadata", return_value=data
    ):
        plotted = maker_class().make_trace(setup, trace)

    for coordinate in coordinates:
        assert len(getattr(plotted, coordinate)) == 0
    assert len(plotted.customdata) == 0


def test_empty_filter_result_skips_density_contours():
    data = pd.DataFrame({"Sol": [4750, 4831]})
    setup = SetupMenuModel()
    trace = TraceEditorModel(density_contour_on=True, filters_on=True, filters=[
        FilterModel(filter_column="Sol", filter_operation="<", filter_value1="4743"),
    ])
    maker = DensityContourMaker()
    with patch.object(
        setup.data_library.dataframe_manager, "get_dataframe_by_metadata", return_value=data
    ), patch.object(maker, "compute_kde_contours") as compute_contours:
        assert maker.make_trace(setup, trace, "empty-trace") is None

    compute_contours.assert_not_called()

"""Independent numerical expectations and actual Plotly trace integration."""

from copy import deepcopy
import json
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from quick_ternaries.models.filter_model import FilterModel
from quick_ternaries.models.setup_menu_model import SetupMenuModel
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.services import heatmap
from quick_ternaries.services.cartesian_trace_maker import CartesianTraceMaker
from quick_ternaries.services.ternary_trace_maker import TernaryTraceMaker
from quick_ternaries.utils.utils import WorkspaceManager
from quick_ternaries.workspace.schema import TRACE_FIELDS


def calculated(**changes):
    return TraceEditorModel(**{
        'heatmap_on': True, 'heatmap_column': 'A', 'heatmap_calculation_on': True,
        'heatmap_columns': ['A', 'B'], 'heatmap_scales': {'A': 2, 'B': .5},
        'heatmap_min': -17, 'heatmap_max': 91, **changes,
    })


def setup_for(data):
    setup = SetupMenuModel()
    setup.axis_members.top_axis = ['A']
    setup.axis_members.left_axis = ['B']
    setup.axis_members.right_axis = ['C']
    setup.axis_members.x_axis = ['A']
    setup.axis_members.y_axis = ['B']
    setup.axis_members.hover_data = ['A', 'B', 'C']
    return setup


def test_weighted_sum_requires_every_component_and_preserves_source():
    data = pd.DataFrame({'A': [1, 2, np.nan, 4, np.inf], 'B': [10, np.nan, 30, 40, 50]})
    original = data.copy(deep=True)
    values, _ = heatmap.color_values(calculated(), data)
    np.testing.assert_allclose(values, [7, np.nan, np.nan, 28, np.nan], equal_nan=True)
    pd.testing.assert_frame_equal(data, original)


def test_molar_components_are_scaled_and_divided_individually_without_normalization():
    # Independent standard molecular masses: one mole water and two moles salt.
    data = pd.DataFrame({'water': [18.01528, 36.03056], 'salt': [116.88554, 58.44277]})
    model = calculated(heatmap_columns=['water', 'salt'],
        heatmap_scales={'water': 2, 'salt': .5},
        heatmap_formulas={'water': 'H2O', 'salt': 'NaCl'}, heatmap_molar=True)
    values, label = heatmap.color_values(model, data)
    np.testing.assert_allclose(values, [3, 4.5], rtol=1e-4)
    assert 'mol/100 g' in label and 'M(H2O)' in label
    assert model.convert_from_wt_to_molar is False


def test_feot_alias_and_nullable_numeric_values():
    data = pd.DataFrame({'A': pd.Series([71.844, None], dtype='Float64')})
    model = calculated(heatmap_columns=['A'], heatmap_scales={}, heatmap_molar=True,
                       heatmap_formulas={'A': 'FeOT'})
    values, _ = heatmap.color_values(model, data)
    assert values.iloc[0] == pytest.approx(1, rel=1e-4)
    assert pd.isna(values.iloc[1])


@pytest.mark.parametrize('maker_class', [TernaryTraceMaker, CartesianTraceMaker])
def test_molar_heatmap_agrees_with_axis_calculation_but_has_independent_switch(maker_class):
    data = pd.DataFrame({'A': [18.01528, 36.03056], 'B': [116.88554, 58.44277], 'C': [10., 20.]})
    setup = setup_for(data)
    for axis in ('top_axis', 'x_axis'):
        setattr(setup.axis_members, axis, ['A', 'B'])
        setup.column_scaling.scaling_factors[axis] = {'A': 2, 'B': .5}
    for axis in ('top_axis', 'left_axis', 'right_axis', 'x_axis', 'y_axis'):
        setup.chemical_formulas.formulas[axis] = {'A': 'H2O', 'B': 'NaCl', 'C': 'SiO2'}
    model = calculated(heatmap_molar=True, heatmap_formulas={'A': 'H2O', 'B': 'NaCl'},
                       heatmap_range_mode='Filtered data', convert_from_wt_to_molar=True)
    with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
        maker = maker_class()
        trace = maker.make_trace(setup, model)
        coordinate = trace.a if maker_class is TernaryTraceMaker else trace.x
        np.testing.assert_allclose(coordinate, trace.marker.color)
        np.testing.assert_allclose(trace.marker.color, [3, 4.5], rtol=1e-4)
        model.convert_from_wt_to_molar = False
        raw_axes = maker.make_trace(setup, model)
        np.testing.assert_allclose(raw_axes.marker.color, trace.marker.color)
        assert list(raw_axes.a if maker_class is TernaryTraceMaker else raw_axes.x) != list(coordinate)


def test_all_invalid_values_fail_and_empty_filters_have_no_invented_range():
    data = pd.DataFrame({'A': [np.nan], 'B': [2.]})
    model = calculated(heatmap_range_mode='Filtered data')
    with pytest.raises(heatmap.HeatmapError, match='No valid'):
        heatmap.resolve(model, data, data)
    empty = heatmap.resolve(model, data.iloc[:0], data)
    assert empty.values.empty and np.isnan(empty.minimum) and np.isnan(empty.maximum)


@pytest.mark.parametrize('changes,message', [
    ({'heatmap_columns': []}, 'Select'),
    ({'heatmap_columns': ['A', 'A']}, 'distinct'),
    ({'heatmap_columns': ['missing']}, 'missing'),
    ({'heatmap_columns': ['text']}, 'numeric'),
    ({'heatmap_scales': {'A': float('inf')}}, 'scale'),
    ({'heatmap_scales': {'A': 0}}, 'scale'),
    ({'heatmap_molar': True, 'heatmap_formulas': {'A': 'H2O'}}, 'formula'),
    ({'heatmap_molar': True, 'heatmap_formulas': {'A': 'invalid!', 'B': 'H2O'}}, 'formula'),
])
def test_invalid_calculations_fail_explicitly(changes, message):
    with pytest.raises(heatmap.HeatmapError, match=message):
        heatmap.color_values(calculated(**changes), pd.DataFrame({'A': [1], 'B': [2], 'text': ['x']}))


@pytest.mark.parametrize('mode,expected', [('Manual', (-17, 91)), ('Full dataset', (7, 28)), ('Filtered data', (7, 14))])
def test_range_scope_uses_final_values_and_never_overwrites_saved_limits(mode, expected):
    data = pd.DataFrame({'A': [1, 2, 4], 'B': [10, 20, 40]})
    model = calculated(heatmap_range_mode=mode)
    before = deepcopy(model.to_dict())
    result = heatmap.resolve(model, data.iloc[:2], data)
    assert (result.minimum, result.maximum) == expected
    assert model.to_dict() == before


@pytest.mark.parametrize('maker_class', [TernaryTraceMaker, CartesianTraceMaker])
@pytest.mark.parametrize('sizes', [False, True])
@pytest.mark.parametrize('sort', ['no change', 'high on top', 'low on top', 'shuffled'])
def test_render_keeps_coordinates_colors_sizes_hover_and_row_ids_aligned(maker_class, sizes, sort):
    data = pd.DataFrame({'A': [1., 2., 3., 4.], 'B': [10., 20., np.nan, 40.],
                         'C': [8., 9., 10., 11.], 'size': [2., 4., 8., 16.]}, index=[11, 13, 23, 42])
    original = data.copy(deep=True)
    setup = setup_for(data)
    # Deliberately different axis coefficients must never affect heatmap values.
    setup.column_scaling.set_scale('x_axis', 'A', 3)
    setup.column_scaling.set_scale('top_axis', 'A', 3)
    model = calculated(heatmap_range_mode='Filtered data', heatmap_sort_mode=sort,
        sizemap_on=sizes, sizemap_column='size', sizemap_sort_mode=sort,
        sizemap_min=2, sizemap_max=6)
    with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
        trace = maker_class().make_trace(setup, model)
    assert len(trace.marker.color) == 3
    assert (trace.marker.cmin, trace.marker.cmax) == (7, 28)
    assert '2 × A + 0.5 × B' in trace.marker.colorbar.title.text
    for i, custom in enumerate(trace.customdata):
        row = data.loc[int(custom[-1])]
        expected = 2 * row.A + .5 * row.B
        assert trace.marker.color[i] == expected
        assert float(custom[-2]) == expected
        coordinate = trace.a[i] if maker_class is TernaryTraceMaker else trace.x[i]
        assert coordinate == 3 * row.A
        if sizes:
            assert trace.marker.size[i] == pytest.approx(2 + (row['size'] - 2) / 14 * 4)
    pd.testing.assert_frame_equal(data, original)


@pytest.mark.parametrize('maker_class', [TernaryTraceMaker, CartesianTraceMaker])
@pytest.mark.parametrize('mode,maximum', [('Filtered data', 14), ('Full dataset', 28)])
@pytest.mark.parametrize('calculation', [False, True])
def test_real_filters_control_range_scope(maker_class, mode, maximum, calculation):
    data = pd.DataFrame({'A': [1., 2., 4.], 'B': [10., 20., 40.], 'C': [3., 4., 5.]})
    setup = setup_for(data)
    model = calculated(heatmap_range_mode=mode, heatmap_calculation_on=calculation, filters_on=True,
        filters=[FilterModel(filter_column='A', filter_operation='<', filter_value1='3')])
    with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
        trace = maker_class().make_trace(setup, model)
        assert list(trace.marker.color) == ([7, 14] if calculation else [1, 2])
        assert trace.marker.cmax == (maximum if calculation else maximum / 7)
        model.filters[0].filter_value1 = '0'
        empty = maker_class().make_trace(setup, model)
        assert len(empty.a if maker_class is TernaryTraceMaker else empty.x) == 0


def test_empty_custom_rgb_trace_does_not_evaluate_inactive_heatmap():
    data = pd.DataFrame({'A': [1.], 'B': [2.], 'C': [3.]})
    setup = setup_for(data)
    model = calculated(custom_colorscale_on=True, heatmap_columns=['absent'],
        filters_on=True, filters=[FilterModel(filter_column='A', filter_operation='<', filter_value1='0')])
    with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
        trace = TernaryTraceMaker().make_trace(setup, model)
    assert len(trace.a) == 0


@pytest.mark.parametrize('maker_class', [TernaryTraceMaker, CartesianTraceMaker])
def test_advanced_log_limits_and_hover_use_consistent_units(maker_class):
    data = pd.DataFrame({'A': [-1., 1., 10., 100.], 'B': [2., 3., 4., 5.], 'C': [3., 4., 5., 6.]})
    setup = setup_for(data)
    model = calculated(heatmap_columns=['A'], heatmap_scales={}, heatmap_log_transform=True,
                       heatmap_min=1, heatmap_max=100)
    with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
        trace = maker_class().make_trace(setup, model)
    np.testing.assert_allclose(trace.marker.color, np.log([1, 10, 100]))
    assert (trace.marker.cmin, trace.marker.cmax) == pytest.approx((0, np.log(100)))
    np.testing.assert_allclose(np.asarray(trace.customdata)[:, -2].astype(float), [1, 10, 100])
    assert trace.marker.colorbar.title.text == 'ln(A)'
    model.heatmap_min = 0
    with pytest.raises(heatmap.HeatmapError, match='positive'):
        heatmap.resolve(model, data, data)


@pytest.mark.parametrize('maker_class', [TernaryTraceMaker, CartesianTraceMaker])
def test_constant_color_and_size_and_duplicate_indices_are_valid(maker_class):
    data = pd.DataFrame({'A': [1., 1.], 'B': [2., 2.], 'C': [3., 3.]}, index=[9, 9])
    setup = setup_for(data)
    model = calculated(heatmap_range_mode='Filtered data', sizemap_on=True,
                       sizemap_column='B', sizemap_min=2, sizemap_max=6)
    with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
        trace = maker_class().make_trace(setup, model)
    assert list(trace.marker.color) == [3, 3]
    assert trace.marker.cmin < 3 < trace.marker.cmax
    assert list(trace.marker.size) == [2, 2]
    assert np.isfinite(trace.marker.sizeref)


@pytest.mark.parametrize('maker_class', [TernaryTraceMaker, CartesianTraceMaker])
@pytest.mark.parametrize('log', [False, True])
def test_old_workspace_preserves_legacy_colors_limits_and_round_trip(maker_class, log):
    # Literal pre-feature workspace fields; deliberately not generated by the new model.
    saved = {'version': '1.0', 'traces': [{'trace_name': 'Saved heatmap', 'heatmap_on': True,
        'heatmap_column': 'color', 'heatmap_min': -5, 'heatmap_max': 20,
        'heatmap_log_transform': log, 'heatmap_reverse_colorscale': False}], 'setup': {}}
    workspace = WorkspaceManager.from_dict(saved)
    model = workspace.traces[0]
    assert not model.heatmap_calculation_on and not model.heatmap_molar
    assert model.heatmap_range_mode == 'Manual'
    restored = WorkspaceManager.from_dict(json.loads(json.dumps(workspace.to_dict()))).traces[0]
    data = pd.DataFrame({'A': [1., 2., 3.], 'B': [2., 3., 4.], 'C': [3., 4., 5.], 'color': [-3., 2., 4.]})
    setup = setup_for(data)
    for trace_model in (model, restored):
        with patch.object(setup.data_library.dataframe_manager, 'get_dataframe_by_metadata', return_value=data):
            trace = maker_class().make_trace(setup, trace_model)
        np.testing.assert_allclose(trace.marker.color, [0, np.log(2), np.log(4)] if log else [-3, 2, 4])
        assert (trace.marker.cmin, trace.marker.cmax) == (-5, 20)


def test_new_workspace_settings_round_trip_and_duplicate_without_aliases():
    model = calculated(heatmap_molar=True, heatmap_formulas={'A': 'H2O', 'B': 'NaCl'},
                       heatmap_range_mode='Filtered data')
    workspace = WorkspaceManager([model], SetupMenuModel())
    restored = WorkspaceManager.from_dict(json.loads(json.dumps(workspace.to_dict()))).traces[0]
    assert restored.to_dict() == model.to_dict()
    restored.heatmap_scales['A'] = 9
    restored.heatmap_columns.append('C')
    assert model.heatmap_scales['A'] == 2 and model.heatmap_columns == ['A', 'B']


@pytest.mark.parametrize('field,value', [('heatmap_scales', {'A': float('nan')}),
    ('heatmap_scales', {'A': -1}), ('heatmap_scales', {'A': True}),
    ('heatmap_formulas', {'A': 4}), ('heatmap_columns', ['A', 'A']),
    ('heatmap_range_mode', 'unknown')])
def test_agent_schema_rejects_invalid_shapes_and_values(field, value):
    with pytest.raises(ValueError):
        TRACE_FIELDS[field].validate(value)

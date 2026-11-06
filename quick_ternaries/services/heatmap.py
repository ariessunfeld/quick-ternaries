"""Opt-in heatmap calculations; legacy single-column rendering stays unchanged."""

from copy import copy
from dataclasses import dataclass
from html import escape
import math

import numpy as np
import pandas as pd

from .molar_mass_calculator import MolarMassCalculator, MolarMassCalculatorException

RANGE_MODES = ('Manual', 'Full dataset', 'Filtered data')
CALCULATION_FIELDS = frozenset({
    'heatmap_calculation_on', 'heatmap_columns', 'heatmap_scales',
    'heatmap_formulas', 'heatmap_molar',
})


class HeatmapError(ValueError):
    """A heatmap cannot be evaluated with its requested configuration."""


def is_advanced(model):
    return model.heatmap_on and (model.heatmap_calculation_on or model.heatmap_range_mode != 'Manual')


def initialize_edit(model, changes):
    """Initialize only on a user gesture, never on loading or refreshing a view."""
    changes = dict(changes)
    if changes.get('heatmap_calculation_on') and not model.heatmap_columns and 'heatmap_columns' not in changes:
        column = changes.get('heatmap_column', model.heatmap_column)
        changes['heatmap_columns'] = [column] if column else []
    if 'heatmap_columns' in changes and 'heatmap_formulas' not in changes:
        from quick_ternaries.utils.functions import suggest_formula_from_column_name
        formulas = dict(model.heatmap_formulas)
        for column in changes['heatmap_columns']:
            if column not in formulas:
                formulas[column] = suggest_formula_from_column_name(column)
        changes['heatmap_formulas'] = formulas
    return changes


def preview(model, frame):
    # Both trace makers currently use the same filter implementation. Call it
    # here as well so limits shown in the editor match the rendered subset.
    from .ternary_trace_maker import TernaryTraceMaker
    filtered = TernaryTraceMaker()._apply_filters(frame, model) if model.filters_on else frame
    return resolve(model, filtered, frame)


def color_values(model, frame):
    """Return unnormalized values and a label, without changing source data.

    A missing/nonfinite component invalidates the entire row. In particular,
    pandas' default skip-NaN sum must not silently produce a partial analysis.
    """
    columns = model.heatmap_columns if model.heatmap_calculation_on else [model.heatmap_column]
    if not columns or len(columns) != len(set(columns)):
        raise HeatmapError('Select at least one distinct heatmap column.')
    terms, labels = [], []
    calculator = MolarMassCalculator()
    for column in columns:
        if column not in frame.columns:
            raise HeatmapError(f'Heatmap column {column!r} is missing from this dataset.')
        if not pd.api.types.is_numeric_dtype(frame[column]):
            raise HeatmapError(f'Heatmap column {column!r} must be numeric.')
        scale = model.heatmap_scales.get(column, 1.0) if model.heatmap_calculation_on else 1.0
        if type(scale) not in (int, float) or not math.isfinite(scale) or not .01 <= scale <= 1000:
            raise HeatmapError(f'Heatmap scale for {column!r} must be between 0.01 and 1000.')
        mass = 1.0
        label = f'{scale:g} × {column}' if scale != 1 else column
        if model.heatmap_calculation_on and model.heatmap_molar:
            formula = model.heatmap_formulas.get(column, '')
            try:
                mass = calculator.get_molar_mass(formula)
                if not math.isfinite(mass) or mass <= 0:
                    raise ValueError('Molar mass must be positive.')
            except (MolarMassCalculatorException, ValueError, TypeError) as exc:
                raise HeatmapError(f'Heatmap column {column!r} needs a valid chemical formula.') from exc
            label = f'{label} / M({formula})'
        # Float conversion also supports pandas nullable numeric columns.
        values = frame[column].to_numpy(dtype=float, na_value=np.nan)
        with np.errstate(over='ignore', invalid='ignore'):
            terms.append(values * scale / mass)
        labels.append(label)
    with np.errstate(over='ignore', invalid='ignore'):
        result = np.sum(terms, axis=0)
    result[~np.isfinite(result)] = np.nan
    label = ' + '.join(labels)
    if model.heatmap_calculation_on and model.heatmap_molar:
        label += ' (mol/100 g; wt% input)'
    return pd.Series(result, index=frame.index, dtype=float), label


@dataclass
class HeatmapValues:
    values: pd.Series
    label: str
    minimum: float
    maximum: float
    excluded: int


def resolve(model, filtered, full):
    """Resolve physical bounds; log mapping is applied only at rendering time."""
    if model.heatmap_range_mode not in RANGE_MODES:
        raise HeatmapError('Unknown heatmap range mode.')
    values, label = color_values(model, filtered)
    if model.heatmap_log_transform:
        values = values.where(values > 0)
    if len(values) and not values.notna().any():
        raise HeatmapError('No valid heatmap values remain; check missing values and log-scale positivity.')
    if model.heatmap_range_mode == 'Manual':
        low, high = model.heatmap_min, model.heatmap_max
        if not all(math.isfinite(v) for v in (low, high)) or low > high:
            raise HeatmapError('Heatmap limits must be finite, with minimum ≤ maximum.')
        if model.heatmap_log_transform and low <= 0:
            raise HeatmapError('Logarithmic heatmap limits must both be positive (enter unlogged values).')
    else:
        reference = color_values(model, full)[0] if model.heatmap_range_mode == 'Full dataset' else values
        if model.heatmap_log_transform:
            reference = reference.where(reference > 0)
        finite = reference.dropna()
        # An empty filtered trace renders no markers and no invented range.
        low, high = (float(finite.min()), float(finite.max())) if len(finite) else (math.nan, math.nan)
    return HeatmapValues(values, label, low, high, int(values.isna().sum()))


def render(maker, marker, model, data, full, unique_str):
    """Reuse marker styling/sorting while keeping all row-dependent arrays aligned."""
    resolved = resolve(model, data, full)
    if data.empty:
        return marker, data
    valid = resolved.values.notna().to_numpy()
    data = data.iloc[np.flatnonzero(valid)].copy()
    value_column = f'__heatmap_value_{unique_str}'
    color_column = f'__heatmap_color_{unique_str}'
    data[value_column] = resolved.values.to_numpy()[valid]
    data[color_column] = np.log(data[value_column]) if model.heatmap_log_transform else data[value_column]
    low, high = resolved.minimum, resolved.maximum
    if model.heatmap_log_transform:
        low, high = math.log(low), math.log(high)
    # Plotly needs a nonzero interval even when every value is identical.
    if low == high:
        delta = max(abs(low) * 1e-6, 1e-6)
        low, high = low - delta, high + delta
    proxy = copy(model)
    proxy.heatmap_column = color_column
    proxy.heatmap_log_transform = False
    proxy.heatmap_min, proxy.heatmap_max = low, high
    marker, data = maker._update_marker_with_heatmap(marker, proxy, data, unique_str)
    if model.sizemap_on:
        # Match the existing order: heatmap ordering first, size ordering last.
        # Keep both arrays in the frame until all sorting is complete.
        sizes = pd.to_numeric(data[model.sizemap_column], errors='coerce').astype(float)
        sizes = sizes.replace([np.inf, -np.inf], np.nan)
        if getattr(model, 'sizemap_log_transform', False):
            sizes = np.log(sizes.where(sizes > 0)).fillna(0)
        lower, upper = float(model.sizemap_min), float(model.sizemap_max)
        if lower > upper:
            raise HeatmapError('Sizemap minimum must not exceed its maximum.')
        span = sizes.max() - sizes.min()
        sizes = ((sizes - sizes.min()) / span * (upper - lower) + lower
                 if span > 0 else pd.Series(lower, index=data.index))
        size_column = f'__heatmap_size_{unique_str}'
        data[size_column] = sizes.fillna(lower)
        if model.sizemap_sort_mode in ('high on top', 'low on top'):
            data = data.sort_values(size_column, ascending=model.sizemap_sort_mode == 'high on top')
        elif model.sizemap_sort_mode == 'shuffled':
            data = data.sample(frac=1)
        marker.update(size=data[size_column], sizemin=lower,
                      sizeref=2 * data[size_column].max() / upper**2 if upper > 0 else 1)
        marker['color'] = data[color_column]
    label = f'ln({resolved.label})' if model.heatmap_log_transform else resolved.label
    marker['colorbar']['title']['text'] = escape(label)
    data.attrs['heatmap_value'] = (value_column, resolved.label)
    return marker, data


def add_hover(data, customdata, template):
    """Insert calculated values before the final source-row identity column."""
    if 'heatmap_value' not in data.attrs or not len(data):
        return customdata, template
    column, label = data.attrs['heatmap_value']
    position = customdata.shape[1] - 1
    customdata = np.column_stack((customdata[:, :position], data[column].to_numpy(), customdata[:, position:]))
    extra = f'<br><b>{escape(label)}:</b> %{{customdata[{position}]}}'
    return customdata, template.replace('<extra></extra>', extra + '<extra></extra>')

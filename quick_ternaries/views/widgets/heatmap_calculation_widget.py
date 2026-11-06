"""The same component controls as axes, scoped to one trace's heatmap."""

from copy import deepcopy
from PySide6.QtCore import Signal, QSignalBlocker
from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QLabel

from .multi_field_selector_widget import MultiFieldSelector
from .column_scaling_widget import ColumnScalingWidget
from .formula_input_widget import FormulaInputWidget
from quick_ternaries.views.accessibility import describe_control


class HeatmapCalculationWidget(QWidget):
    edited = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = None
        self.refreshing = False
        self.columns = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.selector = MultiFieldSelector(self)
        self.selector.set_accessible_field('trace.heatmap_columns', 'Heatmap columns')
        layout.addWidget(self.selector)
        self.scaling = ColumnScalingWidget(self, identifier_prefix='trace.heatmap')
        layout.addWidget(self.scaling)
        self.molar = QCheckBox('Convert heatmap from wt% to molar', self)
        describe_control(self.molar, 'trace.heatmap_molar', self.molar.text())
        layout.addWidget(self.molar)
        self.formulas = FormulaInputWidget(self, identifier_prefix='trace.heatmap', auto_suggest=False)
        layout.addWidget(self.formulas)
        self.help = QLabel('Each component is multiplied by its scale, optionally divided by its molar mass, then summed. Molar values are mol/100 g for wt% inputs; no normalization is applied.')
        self.help.setWordWrap(True)
        layout.addWidget(self.help)
        self.selector.selectionChanged.connect(lambda columns: self.emit_edit({'heatmap_columns': columns}))
        self.scaling.scaleChanged.connect(lambda _, column, value: self.mapping_edit('heatmap_scales', column, value))
        self.formulas.formulaChanged.connect(lambda _, column, value: self.mapping_edit('heatmap_formulas', column, value))
        self.molar.toggled.connect(lambda value: self.emit_edit({'heatmap_molar': value}))

    def emit_edit(self, changes):
        if not self.refreshing:
            self.edited.emit(changes)

    def mapping_edit(self, field, column, value):
        if self.refreshing or self.model is None:
            return
        values = deepcopy(getattr(self.model, field))
        values[column] = value
        self.emit_edit({field: values})

    def refresh(self, model, available):
        self.refreshing = True
        try:
            self.model = model
            self.selector.set_available_options(available)
            with QSignalBlocker(self.selector):
                if self.selector.get_selected_fields() != model.heatmap_columns:
                    self.selector.set_selected_fields(model.heatmap_columns)
            if self.columns != model.heatmap_columns:
                self.columns = list(model.heatmap_columns)
                self.scaling.update_columns('heatmap', self.columns, model.heatmap_scales)
                self.formulas.update_columns('heatmap', self.columns, model.heatmap_formulas)
            else:
                for column in self.columns:
                    self.scaling.set_scale_value('heatmap', column, model.heatmap_scales.get(column, 1.0))
                    self.formulas.set_formula_value('heatmap', column, model.heatmap_formulas.get(column, ''))
            with QSignalBlocker(self.molar):
                self.molar.setChecked(model.heatmap_molar)
            self.formulas.setVisible(model.heatmap_molar)
        finally:
            self.refreshing = False

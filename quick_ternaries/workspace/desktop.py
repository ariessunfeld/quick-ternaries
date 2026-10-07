"""Qt adapter: bind existing models to commands and update only changed controls."""

from copy import copy, deepcopy
from dataclasses import asdict

from PySide6.QtCore import QObject, QEvent, Qt, QSignalBlocker
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit, QAbstractSpinBox, QComboBox, QCheckBox, QListWidgetItem

from .schema import TRACE_FIELDS, PLOT_FIELDS
from .session import Resource, WorkspaceError
from quick_ternaries.models.filter_model import FilterModel
from quick_ternaries.models.trace_editor_model import TraceEditorModel
from quick_ternaries.views.widgets import ColorButton, ColorScaleDropdown, ShapeButtonWithMenu, MultiFieldSelector


class DesktopWorkspace(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window, self.session = window, window.workspace_session
        self.updating = False
        self.gesture = 0
        self.session.trace_resource = self.trace_resource
        self.session.register('plot', None, Resource(self.plot_values, self.write_plot, PLOT_FIELDS, self.validate_plot))
        self.session.changed = self.changed
        self.undoAction = QAction('Undo', window)
        self.redoAction = QAction('Redo', window)
        self.undoAction.setObjectName('workspace.undo')
        self.redoAction.setObjectName('workspace.redo')
        self.undoAction.setShortcuts(QKeySequence.StandardKey.Undo)
        self.redoAction.setShortcuts(QKeySequence.StandardKey.Redo)
        self.undoAction.triggered.connect(lambda: self.move_history(False))
        self.redoAction.triggered.connect(lambda: self.move_history(True))
        menu = window.menuBar().addMenu('&Edit')
        menu.addAction(self.undoAction)
        menu.addAction(self.redoAction)
        window.installEventFilter(self)
        QApplication.instance().focusChanged.connect(self.focus_changed)
        window.tabPanel.listWidget.model().rowsMoved.connect(self.order_changed)
        from .render import RenderService
        self.render = RenderService(window, self.session)
        self.watch_editors()
        self.update_actions()

    def trace_resource(self, model):
        fields = {k: f for k, f in TRACE_FIELDS.items() if hasattr(model, k) or k == 'error_entries'}
        def read():
            return {k: [asdict(f) for f in model.filters] if k == 'filters' else deepcopy(model.error_entry_model.entries) if k == 'error_entries'
                    else deepcopy(getattr(model, k)) for k in fields}
        def write(values):
            for k, value in values.items():
                if k == 'error_entries':
                    model.error_entry_model.entries = deepcopy(value)
                elif k == 'filters':
                    # Preserve existing filter objects while only their values change.
                    if len(model.filters) == len(value):
                        for filt, item in zip(model.filters, value):
                            for field, val in item.items():
                                setattr(filt, field, deepcopy(val))
                    else:
                        model.filters = [FilterModel(**deepcopy(f)) for f in value]
                else:
                    setattr(model, k, value)
        def validate(values, changed, actor):
            data = self.window.setupMenuModel.data_library.dataframe_manager.get_dataframe(model.datafile.df_id)
            columns = set(data.columns) if data is not None else set()
            if actor == 'agent':
                for feature in ('heatmap', 'sizemap'):
                    if changed & {feature + '_on', feature + '_column'} and values[feature + '_on']:
                        column = values[feature + '_column']
                        if column not in columns or data is None or data[column].dtype.kind not in 'biuf':
                            raise WorkspaceError('invalid_command', f'{feature} requires a loaded numeric column.')
                    if changed & {feature + '_min', feature + '_max'} and values[feature + '_min'] > values[feature + '_max']:
                        raise WorkspaceError('invalid_command', f'{feature} minimum must not exceed its maximum.')
                if 'error_entries' in changed and set(values['error_entries']) - columns:
                    raise WorkspaceError('invalid_command', 'Uncertainties must reference loaded columns.')
                if 'filters' in changed:
                    for filt in values['filters']:
                        if not filt['filter_column'] or filt['filter_column'] not in columns or not filt['filter_operation']:
                            raise WorkspaceError('invalid_command', 'Each filter needs a loaded column and an operation.')
                        op = filt['filter_operation']
                        if isinstance(filt['filter_value1'], list) != (op in ('is one of', 'is not one of')):
                            raise WorkspaceError('invalid_command', 'Membership filters use string arrays; other filters use strings.')
                        if op in ('<', '>', '<=', '>=', '==') or op.startswith('a '):
                            import math
                            try:
                                if data[filt['filter_column']].dtype.kind not in 'biuf':
                                    raise ValueError()
                                nums = [float(filt['filter_value1'])]
                                if op.startswith('a '):
                                    nums.append(float(filt['filter_value2']))
                                if not all(math.isfinite(v) for v in nums) or (len(nums) == 2 and nums[0] > nums[1]):
                                    raise ValueError()
                            except (TypeError, ValueError):
                                raise WorkspaceError('invalid_command', 'Numeric filters need finite ordered numeric bounds.') from None
                if 'density_contour_percentiles' in changed:
                    import math
                    try:
                        levels = [float(s.strip()) for s in values['density_contour_percentiles'].split(',')]
                        if not 1 <= len(levels) <= 20 or not all(math.isfinite(v) and 0 < v < 100 for v in levels):
                            raise ValueError()
                    except ValueError:
                        raise WorkspaceError('invalid_command', 'Use 1–20 comma-separated percentiles between 0 and 100.') from None
                if 'heatmap_colorscale' in changed:
                    from plotly.colors import get_colorscale
                    try:
                        get_colorscale(values['heatmap_colorscale'])
                    except Exception:
                        raise WorkspaceError('invalid_command', 'Unknown Plotly colorscale.') from None
        return Resource(read, write, fields, validate)

    def plot_owner(self, field):
        setup = self.window.setupMenuModel
        if field == 'plot_type':
            return setup
        return next(section for section in (setup.plot_labels, setup.axis_members, setup.advanced_settings,
                                                 setup.column_scaling, setup.chemical_formulas)
                    if hasattr(section, field))

    def plot_values(self):
        return {k: deepcopy(getattr(self.plot_owner(k), k)) for k in PLOT_FIELDS}

    def write_plot(self, values):
        for k, value in values.items():
            setattr(self.plot_owner(k), k, deepcopy(value))

    def validate_plot(self, values, changed, actor):
        if actor != 'agent':
            return
        library = self.window.setupMenuModel.data_library
        frames = [library.dataframe_manager.get_dataframe(m.df_id) for m in library.loaded_files]
        columns = set.intersection(*(set(f.columns) for f in frames if f is not None)) if any(f is not None for f in frames) else set()
        for axis in ('x', 'y'):
            if changed & {axis + '_axis_min', axis + '_axis_max'} and values[axis + '_axis_min'] >= values[axis + '_axis_max']:
                raise WorkspaceError('invalid_command', 'Axis minimum must be less than maximum.')
        for field in ('scaling_factors', 'formulas'):
            if field in changed:
                if any(set(mapping) - columns for mapping in values[field].values()):
                    raise WorkspaceError('invalid_command', 'Transforms must reference loaded columns.')
                if field == 'formulas':
                    from quick_ternaries.utils.functions import is_valid_formula
                    if any(formula and not is_valid_formula(formula) for mapping in values[field].values() for formula in mapping.values()):
                        raise WorkspaceError('invalid_command', 'Use valid chemical formulas, or empty strings to clear them.')
        if 'zmap_colorscale' in changed:
            from plotly.colors import get_colorscale
            try:
                get_colorscale(values['zmap_colorscale'])
            except Exception:
                raise WorkspaceError('invalid_command', 'Unknown Plotly colorscale.') from None
        for field in changed:
            if hasattr(self.window.setupMenuModel.axis_members, field):
                selected = values[field] if isinstance(values[field], list) else [values[field]] if values[field] else []
                if set(selected) - columns:
                    raise WorkspaceError('invalid_command', 'Axis and hover fields must use columns shared by loaded datasets.')

    def data_boundary(self):
        self.session.reset()
        self.update_actions()

    def find_trace(self, model):
        return next((uid for uid, item in self.session.traces.items() if item is model), None)

    def edit_trace(self, model, values):
        uid = self.find_trace(model)
        if uid is None or self.updating or getattr(self.window, '_agent_loading_workspace', False):
            return False
        values = dict(values)
        # Treat choosing a heatmap column (including first enable) as one gesture,
        # including its derived bounds. The agent supplies these explicitly.
        for feature in ('heatmap', 'sizemap'):
            column_key, on_key = feature + '_column', feature + '_on'
            if column_key in values or (values.get(on_key) and not getattr(model, column_key)):
                frame = self.window.setupMenuModel.data_library.dataframe_manager.get_dataframe(model.datafile.df_id)
                if frame is not None:
                    numeric = list(frame.select_dtypes(include='number').columns)
                    column = values.get(column_key) or (numeric[0] if numeric else '')
                    values[column_key] = column
                    if feature == 'heatmap' and column in numeric:
                        import numpy as np
                        finite = frame[column].replace([np.inf, -np.inf], np.nan).dropna()
                        if not finite.empty:
                            values.update(heatmap_min=float(finite.min()), heatmap_max=float(finite.max()))
        self.human('trace', uid, values)
        return True

    def edit_plot(self, values):
        if self.updating or getattr(self.window, '_agent_loading_workspace', False):
            return False
        values = dict(values)
        # Native axis selection has historically added newly selected columns
        # to hover data. Keep that convenience in the same undoable gesture.
        axes = self.window.setupMenuModel.axis_members
        added = [column for key, columns in values.items()
                 if key in ('x_axis', 'y_axis', 'top_axis', 'left_axis', 'right_axis')
                 for column in columns if column not in getattr(axes, key)]
        if added and 'hover_data' not in values:
            values['hover_data'] = list(dict.fromkeys([*axes.hover_data, *added]))
        self.human('plot', None, values)
        return True

    def human(self, target, uid, values):
        focus = QApplication.focusWidget()
        merge = (self.gesture, target, uid, tuple(values)) if isinstance(focus, (QLineEdit, QAbstractSpinBox)) else None
        try:
            self.session.human_edit(target, uid, values, merge_key=merge)
        except WorkspaceError:
            # Incomplete input belongs in the editor until it becomes valid.
            # Agent requests cannot replace a modified focused editor.
            self.update_actions()

    def focus_changed(self, before, after):
        self.gesture += 1
        if isinstance(before, QAbstractSpinBox):
            before = before.lineEdit()
        if isinstance(before, QLineEdit):
            before.setModified(False)
        self.update_actions()

    def watch_editors(self):
        # Restrict Python event filters to our own editors. A global application
        # filter would also wrap private WebEngine/network QObjects as they die.
        for view in (self.window.traceEditorView, self.window.setupMenuView):
            for editor in view.findChildren(QLineEdit) + view.findChildren(QAbstractSpinBox):
                editor.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and self.window.isActiveWindow():
            redo = event.matches(QKeySequence.StandardKey.Redo)
            undo = event.matches(QKeySequence.StandardKey.Undo)
            if (undo or redo) and not self.native_text_available(redo):
                self.move_history(redo)
                return True
        return False

    def focused_editor(self):
        focus = QApplication.focusWidget()
        if isinstance(focus, QAbstractSpinBox):
            focus = focus.lineEdit()
        return focus if isinstance(focus, QLineEdit) and self.window.isAncestorOf(focus) else None

    def pending_editor(self):
        focus = self.focused_editor()
        return focus is not None and focus.isModified()

    def native_text_available(self, redo):
        focus = self.focused_editor()
        return (focus is not None and not focus.isReadOnly()
                and (focus.isRedoAvailable() if redo else focus.isUndoAvailable()))

    def update_actions(self):
        history = self.session.history()
        for action, kind in ((self.undoAction, 'undo'), (self.redoAction, 'redo')):
            text = self.native_text_available(kind == 'redo')
            label = 'Typing' if text else history[kind + '_label']
            action.setText(kind.title() + (' ' + label if label else ''))
            action.setEnabled(text or bool(history[kind + '_count']))
            actor = history[kind + '_actor']
            action.setToolTip(('Agent' if actor == 'agent' else 'You') + ': ' + label if label else '')

    def move_history(self, redo):
        if self.native_text_available(redo):
            focus = self.focused_editor()
            (focus.redo if redo else focus.undo)()
        else:
            try:
                (self.session.redo if redo else self.session.undo)()
            except WorkspaceError:
                pass
        self.gesture += 1
        self.update_actions()

    def guard_edits(self, edits):
        focus = self.focused_editor()
        if focus is None or not focus.isModified():
            return
        for edit in edits:
            target, uid, fields = edit['target'], edit.get('trace_id'), edit['changes']
            if target == 'trace' and 'trace_name' in fields:
                tabs = self.window.tabPanel.listWidget
                item = tabs.currentItem()
                if item and item.data(Qt.ItemDataRole.UserRole) == uid and self.contains(tabs, focus):
                    raise WorkspaceError('editor_busy', 'The person is renaming this trace. Let them finish.')
            if target == 'trace' and self.find_trace(self.window.traceEditorView.model) == uid:
                view = self.window.traceEditorView
                if any(self.contains(view.widgets.get(k), focus) for k in fields) or any(k.endswith('_on') for k in fields):
                    raise WorkspaceError('editor_busy', 'The person is editing this field. Let them finish.')
                if (('filters' in fields or 'filters_on' in fields) and (self.contains(getattr(view, 'filterEditorContainer', None), focus) or self.contains(getattr(view, 'filterTabWidget', None), focus))):
                    raise WorkspaceError('editor_busy', 'The person is editing filters. Let them finish.')
                if 'error_entries' in fields and self.contains(getattr(view, 'error_entry_widget', None), focus):
                    raise WorkspaceError('editor_busy', 'The person is editing uncertainties. Let them finish.')
            if target == 'plot':
                if (self.contains(self.window.setupMenuView.formulaWidget, focus) or self.contains(self.window.setupMenuView.scalingWidget, focus)):
                    raise WorkspaceError('editor_busy', 'The person is editing scientific transforms. Let them finish.')
                if 'plot_type' in fields or any(self.contains(self.plot_widget(k), focus) for k in fields):
                    raise WorkspaceError('editor_busy', 'The person is editing these plot settings. Let them finish.')

    @staticmethod
    def contains(widget, child):
        return widget is not None and (widget is child or widget.isAncestorOf(child))

    def plot_widget(self, field):
        if field == 'plot_type':
            return self.window.plotTypeSelector
        return next((widgets[field] for widgets in self.window.setupMenuView.section_widgets.values() if field in widgets), None)

    @staticmethod
    def update_widget(widget, value):
        if widget is None:
            return
        with QSignalBlocker(widget):
            if isinstance(widget, QLineEdit):
                if widget.text() != str(value):
                    widget.setText(str(value))
            elif isinstance(widget, QAbstractSpinBox):
                widget.setValue(value)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(value)
            elif isinstance(widget, QComboBox):
                if widget.findText(str(value)) < 0:
                    widget.addItem(str(value))
                widget.setCurrentText(str(value))
            elif isinstance(widget, ColorButton):
                widget.setColor(value)
            elif isinstance(widget, ColorScaleDropdown):
                widget.setColorScale(value)
            elif isinstance(widget, ShapeButtonWithMenu):
                widget.setShape(value)
            elif isinstance(widget, MultiFieldSelector):
                widget.set_selected_fields(value)

    def changed(self, event):
        self.updating = True
        try:
            for change in event['changes']:
                target, uid, fields = change['target'], change['trace_id'], change['fields']
                if target == 'structure':
                    self.sync_tabs()
                elif target == 'trace':
                    model = self.session.traces.get(uid)
                    if model is None:
                        continue
                    if 'trace_name' in fields:
                        self.sync_tab_name(uid, model.trace_name)
                    view = self.window.traceEditorView
                    if view.model is model:
                        for field in fields:
                            if field == 'error_entries':
                                editor = getattr(view, 'error_entry_widget', None)
                                if editor and event['actor'] != 'human':
                                    with QSignalBlocker(editor):
                                        for component in editor.error_inputs:
                                            editor.set_error_value(component, model.error_entry_model.get_error(component))
                            elif field != 'filters':
                                self.update_widget(view.widgets.get(field), getattr(model, field))
                        if 'filters' in fields and event['actor'] != 'human':
                            selected_filter = getattr(view, 'currentFilterIndex', None)
                            view._build_filters_ui()
                            if selected_filter is not None and model.filters:
                                view.filterTabWidget.setCurrentRow(min(selected_filter, len(model.filters) - 1))
                        view.set_plot_type(view.current_plot_type)
                        view._update_filters_visibility()
                elif target == 'plot':
                    values = self.plot_values()
                    for field in fields:
                        self.update_widget(self.plot_widget(field), values[field].title() if field == 'plot_type' else values[field])
                    if 'plot_type' in fields:
                        self.window.on_plot_type_changed(values['plot_type'])
                    self.window.setupMenuView._update_field_visibility()
                    if (any(hasattr(self.window.setupMenuModel.axis_members, k) for k in fields)
                            or (set(fields) & {'scaling_factors', 'formulas'} and event['actor'] != 'human')):
                        self.window.setupMenuView.update_scaling_widget()
                        self.window.setupMenuView.update_formula_widget()
            self.watch_editors()
            self.window.on_trace_color_changed(None)
            self.update_actions()
        finally:
            self.updating = False

    def sync_tab_name(self, uid, name):
        widget = self.window.tabPanel.listWidget
        with QSignalBlocker(widget):
            for index in range(widget.count()):
                item = widget.item(index)
                if item.data(Qt.ItemDataRole.UserRole) == uid:
                    item.setText(name)
                    break

    def sync_tabs(self):
        panel = self.window.tabPanel
        widget = panel.listWidget
        selected = self.window.current_tab_id
        with QSignalBlocker(widget):
            items = {}
            for i in reversed(range(widget.count())):
                item = widget.item(i)
                uid = item.data(Qt.ItemDataRole.UserRole)
                if uid and uid != 'setup-menu-id':
                    items[uid] = widget.takeItem(i)
            for index, uid in enumerate(self.session.order, 1):
                item = items.get(uid) or QListWidgetItem()
                item.setText(self.session.traces[uid].trace_name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                item.setData(Qt.ItemDataRole.UserRole, uid)
                item.setIcon(panel.removeIcon)
                widget.insertItem(index, item)
            panel.select_tab_by_id(selected if selected in self.session.traces else 'setup-menu-id')
        if selected != 'setup-menu-id' and selected not in self.session.traces:
            self.window.on_tab_selected('setup-menu-id')

    def order_changed(self, *args):
        if not self.updating and not getattr(self.window, '_agent_loading_workspace', False):
            widget = self.window.tabPanel.listWidget
            order = [widget.item(i).data(Qt.ItemDataRole.UserRole) for i in range(widget.count())]
            self.session.reorder([uid for uid in order if uid in self.session.order])

    def trace_command(self, operation, arguments, reader):
        if operation == 'delete_trace':
            if set(arguments) != {'trace_id'} or arguments['trace_id'] not in self.session.order:
                raise WorkspaceError('trace_not_found', 'Trace unavailable.')
            uid = arguments['trace_id']
            self.guard_edits([{'target': 'trace', 'trace_id': uid, 'changes': TRACE_FIELDS}])
            self.session.remove_trace(uid, record=True, actor='agent')
            return {'trace_id': uid}
        if operation == 'reorder_traces':
            if set(arguments) != {'trace_ids'}:
                raise WorkspaceError('invalid_command', 'Supply trace_ids in the desired order.')
            self.session.reorder(arguments['trace_ids'], actor='agent')
            return {'trace_order': list(self.session.order)}
        if operation not in ('create_trace', 'duplicate_trace') or set(arguments) != {'source_id', 'name'}:
            raise WorkspaceError('invalid_command', 'Supply source_id (dataset or trace) and name.')
        TRACE_FIELDS['trace_name'].validate(arguments['name'])
        if operation == 'duplicate_trace':
            source = self.session.traces.get(arguments['source_id'])
            if source is None or source.is_contour:
                raise WorkspaceError('invalid_command', 'Choose a regular data trace to duplicate.')
            model = copy(source)
            model.filters = deepcopy(source.filters)
            model.error_entry_model = deepcopy(source.error_entry_model)
            model.source_point_data = deepcopy(source.source_point_data)
        else:
            metadata = next((m for m in self.window.setupMenuModel.data_library.loaded_files
                             if reader.dataset_id(m) == arguments['source_id']), None)
            if metadata is None:
                raise WorkspaceError('dataset_not_found', 'Choose a currently loaded dataset.')
            model = TraceEditorModel(datafile=metadata, trace_color='#377eb8')
        model.trace_name = arguments['name']
        uid = self.session.add_trace(model, record=True, actor='agent')
        return {'trace_id': uid}

"""One render lifecycle for the Render button and the agent adapter."""

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from PySide6.QtCore import QObject, QTimer

from .session import WorkspaceError


class RenderService(QObject):
    def __init__(self, window, session):
        super().__init__(window)
        self.window, self.session = window, session
        self.directory = TemporaryDirectory(prefix='quick-ternaries-plot-')
        self.job = None
        window.plotView.loadFinished.connect(self.loaded)

    def status(self):
        self.session.synchronize()
        if self.job is None:
            return {'status': 'not_rendered'}
        return {**deepcopy(self.job), 'stale': self.job['workspace_epoch'] != self.session.epoch
                or self.job['workspace_revision'] != self.session.revision,
                'revision_scope': 'editable_workspace'}

    def request(self, *, workspace_epoch, request_id, expected_revision):
        return self.session.control(operation='render_plot', workspace_epoch=workspace_epoch,
                                    request_id=request_id, expected_revision=expected_revision,
                                    execute=lambda: self.queue('agent'))

    def from_ui(self):
        if self.job and self.job['status'] in ('queued', 'building', 'loading'):
            return
        self.session.synchronize()
        self.queue('human')

    def queue(self, actor):
        if self.job and self.job['status'] in ('queued', 'building', 'loading'):
            raise WorkspaceError('render_busy', 'A render is already running.')
        # Rendering is an explicit action, not a history entry. Its receipt is
        # still deduplicated, so a transport retry cannot queue duplicate work.
        self.job = {'job_id': str(uuid4()), 'status': 'queued', 'actor': actor,
                    'workspace_epoch': self.session.epoch, 'workspace_revision': self.session.revision}
        job_id = self.job['job_id']
        QTimer.singleShot(0, lambda: self.build(job_id))
        return deepcopy(self.job)

    def build(self, job_id):
        if not self.job or self.job['job_id'] != job_id:
            return
        self.session.synchronize()
        if (self.session.epoch != self.job['workspace_epoch'] or self.session.revision != self.job['workspace_revision']):
            self.job.update(status='cancelled', error='workspace_changed')
            return
        if self.job['status'] != 'queued':
            return
        self.job['status'] = 'building'
        self.window._agent_rendering = self.job['actor'] == 'agent'
        try:
            # Existing scientific plot services remain the source of rendering.
            result = self.window._render_plot()
            if result:
                self.job['status'] = 'loading'
                QTimer.singleShot(15000, lambda: self.expire(job_id))
            else:
                self.job.update(status='failed', error='render_validation_failed')
        except Exception:
            # Scientific/data exceptions may include private file paths or rows.
            self.job.update(status='failed', error='render_failed',
                            message='Check the plot configuration and loaded data.')
        finally:
            self.window._agent_rendering = False

    def loaded(self, ok):
        if not self.job or self.job['status'] != 'loading':
            return
        if not ok:
            if not self.window.plotView.page().isLoading():
                self.job.update(status='failed', error='view_load_failed')
            return
        if self.window.setupMenuModel.plot_type == 'zmap':
            self.job['status'] = 'view_loaded'
            return
        self.check_ready(self.job['job_id'])

    def check_ready(self, job_id):
        if not self.job or self.job['job_id'] != job_id or self.job['status'] != 'loading':
            return
        def received(ready):
            if not self.job or self.job['job_id'] != job_id or self.job['status'] != 'loading':
                return
            if ready:
                self.job['status'] = 'rendered'
                current = job_id + '.html'
                for path in Path(self.directory.name).glob('*.html'):
                    if path.name != current:
                        path.unlink(missing_ok=True)
            else:
                QTimer.singleShot(100, lambda: self.check_ready(job_id))
        self.window.plotView.page().runJavaScript('window.__quick_ternaries_render_ready === true', received)

    def cancel_pending(self):
        # Revocation prevents queued work from starting; an already displayed
        # plot remains the person's workspace output.
        if self.job and self.job['actor'] == 'agent' and self.job['status'] == 'queued':
            self.job.update(status='cancelled', error='permission_revoked')

    def expire(self, job_id):
        if self.job and self.job['job_id'] == job_id and self.job['status'] == 'loading':
            self.job.update(status='failed', error='view_load_timeout')

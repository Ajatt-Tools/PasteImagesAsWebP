# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import qconnect
from aqt.qt import QObject, QRunnable, pyqtSignal

from .convert_task import ConvertTask


class ConvertSignals(QObject):
    canceled = pyqtSignal()
    task_done = pyqtSignal()
    update_progress = pyqtSignal(int)


class ConvertRunnable(QRunnable):
    canceled: bool

    def __init__(self, task: ConvertTask, signals: ConvertSignals):
        super().__init__()
        self.canceled = False
        self.task = task
        self.signals = signals
        qconnect(self.signals.canceled, self.set_canceled)

    def set_canceled(self):
        self.canceled = True
        self.task.set_canceled()

    def run(self):
        for progress_value in self.task():
            if self.canceled:
                break
            self.signals.update_progress.emit(progress_value)  # type: ignore
        self.signals.task_done.emit()  # type: ignore

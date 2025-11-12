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

    def __init__(self, task: ConvertTask, signals: ConvertSignals) -> None:
        super().__init__()
        self.task = task
        self.signals = signals
        qconnect(self.signals.canceled, self.set_canceled)

    def set_canceled(self) -> None:
        self.task.set_canceled()

    def run(self) -> None:
        self.signals.update_progress.emit(0)
        for progress_value in self.task():
            self.signals.update_progress.emit(progress_value)  # type: ignore
        self.signals.task_done.emit()  # type: ignore

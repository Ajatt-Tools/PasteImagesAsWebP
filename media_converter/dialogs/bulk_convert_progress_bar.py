# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import cast

from aqt import qconnect
from aqt.qt import *
from PyQt6.QtWidgets import QWidget

from ..bulk_convert.convert_task import ConvertTask
from ..bulk_convert.runnable import ConvertRunnable, ConvertSignals
from ..consts import ADDON_NAME_SNAKE
from .settings_dialog_base import AnkiSaveAndRestoreGeomDialog


class ProgressBar(AnkiSaveAndRestoreGeomDialog):
    name: str = f"ajt__{ADDON_NAME_SNAKE}_convert_progress_bar"
    task: ConvertTask

    def __init__(self, task: ConvertTask, parent=None) -> None:
        super().__init__(parent)
        self.bar = QProgressBar()
        self.cancel_button = QPushButton("Cancel")
        self.setLayout(self.setup_layout())
        self.task = task
        self.signals = ConvertSignals()
        self.pool = QThreadPool.globalInstance()
        cast(QWidget, self).setWindowTitle("Converting...")
        self.setMinimumSize(320, 24)
        self.move(100, 100)
        self.set_range(0, task.size)
        qconnect(self.cancel_button.clicked, self.set_canceled)
        qconnect(self.signals.task_done, self.accept)
        qconnect(self.signals.update_progress, self.bar.setValue)

    def start_task(self) -> int:
        runnable = ConvertRunnable(self.task, self.signals)
        self.pool.start(runnable)
        return self.exec()

    def set_canceled(self):
        self.signals.canceled.emit()  # type: ignore

    def setup_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addWidget(self.bar)
        layout.addLayout(self.setup_cancel_button_layout())
        return layout

    def setup_cancel_button_layout(self) -> QLayout:
        layout = QHBoxLayout()
        layout.addStretch()
        layout.addWidget(self.cancel_button)
        return layout

    def set_range(self, min_val: int, max_val: int) -> None:
        return self.bar.setRange(min_val, max_val)

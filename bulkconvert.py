# -*- coding: utf-8 -*-

# Paste Images As WebP add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.
import re
import threading
from typing import Optional, Generator, Sequence, Set, Iterable, Dict, Any

from anki.utils import joinFields
from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.qt import *

from .common import tooltip
from .utils.gui import SettingsDialog
from .utils.webp import ImageConverter


def checkpoint(msg="Checkpoint"):
    def decorator(fn):
        def decorated(*args, **kwargs):
            mw.checkpoint(msg)
            fn(*args, **kwargs)
            mw.reset()

        return decorated

    return decorator


class ConvertTask:
    def __init__(self, note_ids: Sequence[Any]):
        self.note_ids = note_ids
        self.to_convert = find_images_to_convert_and_notes(note_ids)
        self.converted: Optional[Dict[str, str]] = None

    @property
    def size(self) -> int:
        return len(self.to_convert)

    def __call__(self):
        self.converted = {}

        for i, filename in enumerate(self.to_convert):
            yield i
            if converted_filename := convert_image(filename):
                self.converted[filename] = converted_filename

    def update_notes(self):
        for initial_filename, converted_filename in self.converted.items():
            for note_id in self.to_convert[initial_filename]:
                note = mw.col.getNote(note_id)
                for key in note.keys():
                    note[key] = note[key].replace(initial_filename, converted_filename)
                note.flush()


class ProgressBar(QDialog):
    task_done = pyqtSignal()
    update_progress = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(ProgressBar, self).__init__(*args, **kwargs)
        self.bar = QProgressBar()
        self.cancel_button = QPushButton('Cancel')
        self.setLayout(self.setup_layout())
        self.canceled = False
        self.task: Optional[ConvertTask] = None
        self.setWindowTitle("Converting...")
        self.setMinimumSize(320, 24)
        self.move(100, 100)
        qconnect(self.cancel_button.clicked, self.set_canceled)
        qconnect(self.task_done, self.accept)
        qconnect(self.update_progress, self.bar.setValue)

    def run(self):
        for progress_value in self.task():
            if self.canceled is True:
                break
            self.update_progress.emit(progress_value)  # type: ignore
        self.task_done.emit()  # type: ignore

    def set_canceled(self):
        self.canceled = True

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


def find_eligible_images(html: str) -> Generator[str, None, None]:
    images = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', html)
    return (image for image in images if image[-5:] != '.webp')


def find_images_to_convert_and_notes(note_ids: Iterable) -> Dict[str, Set[Any]]:
    to_convert = {}

    for note in {mw.col.getNote(note_id) for note_id in note_ids}:
        note_content = joinFields(note.fields)
        if '<img' not in note_content:
            continue
        for filename in find_eligible_images(note_content):
            to_convert[filename] = to_convert.get(filename, set()).union({note.id, })

    return to_convert


def convert_image(filename: str) -> Optional[str]:
    try:
        w = ImageConverter()
        w.load_internal(filename)
        w.convert_internal(filename)
    except RuntimeError:
        pass
    except FileNotFoundError:
        pass
    else:
        return w.filename


@checkpoint(msg="Bulk-convert to WebP")
def bulk_convert(note_ids: Sequence[Any]):
    progress_bar = ProgressBar()
    convert_task = ConvertTask(note_ids)

    progress_bar.set_range(0, convert_task.size)
    progress_bar.task = convert_task

    t = threading.Thread(target=progress_bar.run)
    t.start()

    progress_bar.exec_()
    convert_task.update_notes()
    t.join()

    tooltip(f"Done. Converted {len(convert_task.converted)} files.")


def on_bulk_convert(browser: Browser):
    selected_nids = browser.selectedNotes()
    if selected_nids:
        dialog = SettingsDialog(browser)
        dialog.exec_()
        bulk_convert(selected_nids)
    else:
        tooltip("No cards selected.")


def setup_menu(browser: Browser):
    a = QAction("Bulk-convert to WebP", browser)
    a.triggered.connect(lambda: on_bulk_convert(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)

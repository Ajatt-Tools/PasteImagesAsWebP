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

import functools
import re
import threading
from typing import Optional, Generator, Sequence, Iterable, Dict, Set

from anki.collection import Collection
from anki.notes import Note
from anki.utils import joinFields
from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.operations import CollectionOp, ResultWithChanges
from aqt.qt import *
from aqt.utils import showInfo

from .common import tooltip, NoteId
from .utils.gui import SettingsDialog
from .utils.webp import ImageConverter


class ConvertTask:
    def __init__(self, note_ids: Sequence[NoteId]):
        self.note_ids = note_ids
        self.to_convert = find_images_to_convert_and_notes(note_ids)
        self.converted: Optional[Dict[str, str]] = None
        self.failed: Optional[Dict[str, None]] = None

    @property
    def size(self) -> int:
        return len(self.to_convert)

    def __call__(self):
        self.converted = {}
        self.failed = {}

        for progress, filename in enumerate(self.to_convert):
            yield progress
            if converted_filename := convert_image(filename):
                self.converted[filename] = converted_filename
            else:
                self.failed[filename] = None

    def update_notes_op(self, col: Collection) -> ResultWithChanges:
        pos = col.add_custom_undo_entry(f"Convert {len(self.converted)} images to WebP")
        to_update: Dict[NoteId, Note] = {}

        for initial_filename, converted_filename in self.converted.items():
            for note_id in self.to_convert[initial_filename]:
                if note_id not in to_update:
                    to_update[note_id] = mw.col.getNote(note_id)
                for key in (note := to_update[note_id]).keys():
                    note[key] = note[key].replace(initial_filename, converted_filename)

        col.update_notes(tuple(to_update.values()))
        return col.merge_undo_entries(pos)

    def update_notes(self, parent: QWidget):
        if self.converted:
            CollectionOp(
                parent=parent, op=lambda col: self.update_notes_op(col)
            ).success(
                lambda out: showInfo(
                    parent=parent,
                    title="Task done",
                    textFormat="rich",
                    text=self.form_report_message()
                )
            ).run_in_background()

    def form_report_message(self) -> str:
        text = f"<p>Converted <b>{len(self.converted)}</b> files.</p>"
        if self.failed:
            text += f"<p>Failed <b>{len(self.failed)}</b> files:</p>"
            text += "<ol>"
            text += ''.join(f"<li>{filename}</li>" for filename in self.failed)
            text += "</ol>"
        return text


class ProgressBar(QDialog):
    task_done = pyqtSignal()
    update_progress = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    for image in re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', html):
        if image[-5:] != '.webp':
            yield image


def find_images_to_convert_and_notes(note_ids: Iterable) -> Dict[str, Set[NoteId]]:
    """
    Maps each filename to a set of note ids that reference the filename.
    """
    to_convert = {}

    for note_id, note_content in zip(note_ids, (joinFields(mw.col.getNote(note_id).fields) for note_id in note_ids)):
        if '<img' not in note_content:
            continue
        for filename in find_eligible_images(note_content):
            to_convert[filename] = to_convert.get(filename, set())
            to_convert[filename].add(note_id)

    return to_convert


def convert_image(filename: str) -> Optional[str]:
    try:
        w = ImageConverter()
        w.load_internal(filename)
        w.convert_internal(filename)
    except (RuntimeError, FileNotFoundError):
        pass
    else:
        return w.filename


def reload_note(f: Callable[[Browser, Sequence[NoteId]], None]):
    @functools.wraps(f)
    def decorator(browser: Browser, note_ids: Sequence[NoteId]):
        note = browser.editor.note
        if note:
            browser.editor.set_note(None)
        f(browser, note_ids)
        if note:
            browser.editor.set_note(note)

    return decorator


@reload_note
def bulk_convert(browser: Browser, note_ids: Sequence[NoteId]):
    progress_bar = ProgressBar()
    convert_task = ConvertTask(note_ids)

    progress_bar.set_range(0, convert_task.size)
    progress_bar.task = convert_task

    t = threading.Thread(target=progress_bar.run)
    t.start()

    progress_bar.exec_()
    convert_task.update_notes(browser)
    t.join()


def on_bulk_convert(browser: Browser):
    selected_nids = browser.selectedNotes()
    if selected_nids:
        if SettingsDialog(browser).exec():
            bulk_convert(browser, selected_nids)
    else:
        tooltip("No cards selected.")


def setup_menu(browser: Browser):
    a = QAction("Bulk-convert to WebP", browser)
    qconnect(a.triggered, lambda: on_bulk_convert(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)

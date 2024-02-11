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
import threading
from typing import Sequence, cast

from anki.collection import Collection
from anki.notes import Note, NoteId
from anki.utils import join_fields
from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.operations import CollectionOp, ResultWithChanges
from aqt.utils import showInfo

from .common import *
from .config import config
from .gui import BulkConvertDialog
from .webp import InternalFileConverter


class ConvertResult:
    def __init__(self):
        self._converted: dict[str, str] = {}
        self._failed: dict[str, None] = {}

    def add_converted(self, old_filename: str, new_filename: str):
        self._converted[old_filename] = new_filename

    def add_failed(self, filename: str):
        self._failed[filename] = None

    @property
    def converted(self):
        return self._converted

    @property
    def failed(self) -> Sequence[str]:
        return self._failed

    def is_dirty(self) -> bool:
        return bool(self._converted or self._failed)


class ConvertTask:
    def __init__(self, browser: Browser, note_ids: Sequence[NoteId], selected_fields: list[str]):
        self._browser: Browser = browser
        self._selected_fields: list[str] = selected_fields
        self._to_convert: dict[str, dict[NoteId, Note]] = self._find_images_to_convert_and_notes(note_ids)
        self._result = ConvertResult()

    @property
    def size(self) -> int:
        return len(self._to_convert)

    def __call__(self):
        if self._result.is_dirty():
            raise RuntimeError("Already converted.")

        for progress_idx, filename in enumerate(self._to_convert):
            yield progress_idx
            if converted_filename := self._convert_stored_image(filename, self._first_referenced(filename)):
                self._result.add_converted(filename, converted_filename)
            else:
                self._result.add_failed(filename)

    def update_notes(self):
        def show_report_message():
            showInfo(
                parent=self._browser,
                title="Task done",
                textFormat="rich",
                text=self._form_report_message()
            )

        if self._result.is_dirty():
            if not self._result.converted:
                return show_report_message()
            CollectionOp(
                parent=self._browser, op=lambda col: self._update_notes_op(col)
            ).success(
                lambda out: show_report_message()
            ).run_in_background()

    def _first_referenced(self, filename: str) -> Note:
        return next(note for note in self._to_convert[filename].values())

    def _keys_to_update(self, note: Note) -> Iterable[str]:
        if not self._selected_fields:
            return note.keys()
        else:
            return set(note.keys()).intersection(self._selected_fields)

    def _find_images_to_convert_and_notes(self, note_ids: Sequence[NoteId]) -> dict[str, dict[NoteId, Note]]:
        """
        Maps each filename to a set of note ids that reference the filename.
        """
        to_convert: dict[str, dict[NoteId, Note]] = {}

        for note in map(mw.col.get_note, note_ids):
            note_content = join_fields([note[field] for field in self._keys_to_update(note)])
            if '<img' not in note_content:
                continue
            for filename in find_convertible_images(note_content, include_webp=config['bulk_reconvert_webp']):
                to_convert.setdefault(filename, dict())[note.id] = note

        return to_convert

    def _convert_stored_image(self, filename: str, note: Note) -> Optional[str]:
        try:
            w = InternalFileConverter(self._browser.editor, note)
            w.load_internal(filename)
            w.convert_internal()
        except (OSError, RuntimeError, FileNotFoundError):
            pass
        else:
            return w.filename

    def _update_notes_op(self, col: Collection) -> ResultWithChanges:
        pos = col.add_custom_undo_entry(f"Convert {len(self._result.converted)} images to WebP")
        to_update: dict[NoteId, Note] = {}

        for initial_filename, converted_filename in self._result.converted.items():
            for note in self._to_convert[initial_filename].values():
                for key in self._keys_to_update(note):
                    note[key] = note[key].replace(initial_filename, converted_filename)
                to_update[note.id] = note

        col.update_notes(list(to_update.values()))
        return col.merge_undo_entries(pos)

    def _form_report_message(self) -> str:
        text = f"<p>Converted <b>{len(self._result.converted)}</b> files.</p>"
        if self._result.failed:
            text += f"<p>Failed <b>{len(self._result.failed)}</b> files:</p>"
            text += "<ol>"
            text += ''.join(f"<li>{filename}</li>" for filename in self._result.failed)
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
        cast(QDialog, self).setWindowTitle("Converting...")
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


def reload_note(f: Callable[[Browser, Sequence[NoteId]], None]):
    @functools.wraps(f)
    def decorator(browser: Browser, *args, **kwargs):
        note = browser.editor.note
        if note:
            browser.editor.currentField = None
            browser.editor.set_note(None)
        f(browser, *args, **kwargs)
        if note:
            browser.editor.set_note(note)

    return decorator


@reload_note
def bulk_convert(browser: Browser, note_ids: Sequence[NoteId], selected_fields: list[str]):
    progress_bar = ProgressBar()
    convert_task = ConvertTask(browser, note_ids, selected_fields)

    progress_bar.set_range(0, convert_task.size)
    progress_bar.task = convert_task

    t = threading.Thread(target=progress_bar.run)
    t.start()

    progress_bar.exec()
    convert_task.update_notes()
    browser.editor.loadNoteKeepingFocus()
    t.join()


def on_bulk_convert(browser: Browser):
    selected_nids = browser.selectedNotes()
    if selected_nids:
        dialog = BulkConvertDialog(browser)
        if dialog.exec():
            if len(selected_nids) == 1:
                browser.table.clear_selection()
            bulk_convert(browser, selected_nids, dialog.selected_fields())
    else:
        tooltip("No cards selected.", parent=browser)


def setup_menu(browser: Browser):
    a = QAction("Bulk-convert to WebP", browser)
    qconnect(a.triggered, lambda: on_bulk_convert(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)

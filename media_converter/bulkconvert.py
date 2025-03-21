# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from collections.abc import Sequence

from anki.notes import NoteId
from aqt import gui_hooks
from aqt.browser import Browser
from aqt.qt import *

from .bulk_convert.convert_task import ConvertTask
from .common import tooltip
from .config import config
from .consts import ADDON_FULL_NAME
from .dialogs.bulk_convert_dialog import AnkiBulkConvertDialog
from .dialogs.bulk_convert_progress_bar import ProgressBar

ACTION_NAME = f"{ADDON_FULL_NAME}: Bulk-convert"


def reload_note(func: Callable[[Browser, Sequence[NoteId], list[str]], None]):
    @functools.wraps(func)
    def decorator(browser: Browser, note_ids: Sequence[NoteId], selected_fields: list[str]) -> None:
        assert browser.editor
        note = browser.editor.note
        if note:
            browser.editor.currentField = None
            browser.editor.set_note(None)
        func(browser, note_ids, selected_fields)
        if note:
            browser.editor.set_note(note)

    return decorator


@reload_note
def bulk_convert(browser: Browser, note_ids: Sequence[NoteId], selected_fields: list[str]) -> None:
    progress_bar = ProgressBar(task=ConvertTask(browser, note_ids, selected_fields))
    progress_bar.start_task()  # blocks
    progress_bar.task.update_notes()


def on_bulk_convert(browser: Browser):
    selected_nids = browser.selectedNotes()
    if selected_nids:
        dialog = AnkiBulkConvertDialog(parent=browser, config=config)
        if dialog.exec():
            if len(selected_nids) == 1:
                browser.table.clear_selection()
            bulk_convert(browser, selected_nids, dialog.selected_fields())
    else:
        tooltip("No cards selected.", parent=browser)


def setup_menu(browser: Browser):
    a = QAction(ACTION_NAME, browser)
    qconnect(a.triggered, lambda: on_bulk_convert(browser))
    browser.form.menuEdit.addAction(a)


def init() -> None:
    gui_hooks.browser_menus_did_init.append(setup_menu)

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from collections.abc import Sequence

from anki.notes import NoteId
from aqt import gui_hooks
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import tooltip

from .bulk_convert.convert_task import ConvertTask
from .config import MediaConverterConfig
from .consts import ADDON_FULL_NAME
from .dialogs.bulk_convert_dialog import AnkiBulkConvertDialog
from .dialogs.bulk_convert_progress_bar import ProgressBar

ACTION_NAME = f"{ADDON_FULL_NAME}: Bulk-convert"


def reload_note(func: Callable[["BulkConverter", Sequence[NoteId], list[str]], None]):
    @functools.wraps(func)
    def decorator(self: "BulkConverter", note_ids: Sequence[NoteId], selected_fields: list[str]) -> None:
        assert self._browser.editor
        note = self._browser.editor.note
        if note:
            self._browser.editor.currentField = None
            self._browser.editor.set_note(None)
        func(self, note_ids, selected_fields)
        if note:
            self._browser.editor.set_note(note)

    return decorator


class BulkConverter:
    _config: MediaConverterConfig
    _browser: Browser

    def __init__(self, config: MediaConverterConfig, browser: Browser) -> None:
        self._config = config
        self._browser = browser

    def on_bulk_convert(self) -> None:
        selected_nids = self._browser.selectedNotes()
        if selected_nids:
            dialog = AnkiBulkConvertDialog(parent=self._browser, config=self._config)
            if dialog.exec():
                if len(selected_nids) == 1:
                    self._browser.table.clear_selection()
                self._bulk_convert(selected_nids, dialog.selected_fields())
        else:
            tooltip("No cards selected.", period=self._config.tooltip_duration_milliseconds, parent=self._browser)

    @reload_note
    def _bulk_convert(self, note_ids: Sequence[NoteId], selected_fields: list[str]) -> None:
        progress_bar = ProgressBar(task=ConvertTask(self._browser, note_ids, selected_fields, self._config))
        progress_bar.start_task()  # blocks
        progress_bar.task.update_notes()


def setup_menu(browser: Browser):
    from .config import config

    a = QAction(ACTION_NAME, browser)
    converter = BulkConverter(config=config, browser=browser)
    qconnect(a.triggered, converter.on_bulk_convert)
    browser.form.menuEdit.addAction(a)


def init() -> None:
    gui_hooks.browser_menus_did_init.append(setup_menu)

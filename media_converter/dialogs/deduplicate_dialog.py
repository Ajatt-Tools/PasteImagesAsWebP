# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import typing
from collections.abc import Sequence

import aqt
from aqt.qt import *
from aqt.utils import tooltip

from ..ajt_common.stats_table_dialog import StatsDialog
from ..ajt_common.utils import open_file, ui_translate


class DeduplicateTableColumns(typing.NamedTuple):
    duplicate_name: str
    original_name: str

    @classmethod
    def column_names(cls) -> Sequence[str]:
        return [ui_translate(field) for field in cls.__annotations__]


def copy_cell_to_clipboard(item: typing.Optional[QTableWidgetItem]) -> None:
    if item:
        QApplication.clipboard().setText(item.text())


class DeduplicateMediaConfirmDialog(StatsDialog):
    name: str = "ajt__deduplicate_media_confirm_dialog"
    win_title: str = "Deduplicate media files"
    button_box_buttons: QDialogButtonBox.StandardButton = (
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )

    def __init__(self, column_names: Sequence[str], parent: typing.Optional[aqt.AnkiQt] = None) -> None:
        super().__init__(column_names=column_names, parent=parent)
        self._count_label = QLabel()
        self._layout.insertWidget(0, self._count_label)
        self._setup_context_menu()

    def _setup_context_menu(self) -> None:
        """
        Create right-click context menu actions. The user can copy the contents of a cell to the clipboard.
        """
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        qconnect(self._table.customContextMenuRequested, self._show_context_menu)

    def _show_context_menu(self, pos: QPoint) -> None:
        item = self._table.itemAt(pos)
        if not item:
            return
        menu = QMenu(self._table)

        copy_cell_action = menu.addAction("Copy to the clipboard")
        copy_cell_action.setEnabled(item is not None)
        qconnect(copy_cell_action.triggered, lambda: copy_cell_to_clipboard(item))

        search_action = menu.addAction("Search in Browser")
        search_action.setEnabled(item is not None)
        qconnect(search_action.triggered, lambda: self._search_in_anki_browser(item))

        show_in_fm_action = menu.addAction("Show in file manager")
        show_in_fm_action.setEnabled(item is not None)
        qconnect(show_in_fm_action.triggered, lambda: self._show_in_file_manager(item))

        menu.exec(self._table.viewport().mapToGlobal(pos))

    def _search_in_anki_browser(self, item: typing.Optional[QTableWidgetItem]) -> None:
        """
        Paste selected text into the Browser's search bar and perform search.
        """
        if not aqt.mw:
            # Can't do anything without Anki. Abort.
            return
        if not (item and item.text()):
            tooltip("Empty selection.", parent=self)
        browser = aqt.dialogs.open("Browser", aqt.mw)  # browser requires mw (AnkiQt) to be passed as parent
        browser.activateWindow()
        browser.search_for(item.text())

    def _show_in_file_manager(self, item: typing.Optional[QTableWidgetItem]) -> None:
        if not (item and item.text() and aqt.mw):
            return
        file_path = os.path.join(aqt.mw.col.media.dir(), item.text())
        if os.path.exists(file_path):
            open_file(file_path)
        else:
            tooltip("File does not exist.", parent=self)

    def row_count(self) -> int:
        return self._table.rowCount()

    def load_data(self, data: Sequence[Sequence[str]]) -> "StatsDialog":
        self._count_label.setText(f"Found {len(data)} copies.")
        return super().load_data(data)

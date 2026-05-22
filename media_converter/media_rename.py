# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
import typing
from collections.abc import Iterable
from typing import cast

from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import showCritical, tooltip

from .ajt_common.about_menu import tweak_window
from .ajt_common.monospace_line_edit import MonoSpaceLineEdit
from .ajt_common.utils import open_file
from .consts import ADDON_FULL_NAME, WINDOW_MIN_WIDTH


class FileNameEdit(MonoSpaceLineEdit):
    _edit_max_len = 119

    def __init__(self, text: str):
        super().__init__()
        self.setMaxLength(self._edit_max_len)
        self.setText(text)
        qconnect(self.textChanged, self.validate)
        self._valid = True

    @property
    def valid(self) -> bool:
        return self._valid

    def text(self):
        return super().text().strip("-_ ")

    def validate(self):
        self._valid = len(self.text().encode("utf-8")) <= self._edit_max_len and re.fullmatch(
            r'^[^\[\]<>:\'"/|?*\\]+\.\w{,5}$', self.text()
        )
        if self._valid:
            cast(QWidget, self).setStyleSheet("")
        else:
            cast(QWidget, self).setStyleSheet("background-color: #eb6b60;")


class FileOpenButton(QPushButton):
    def __init__(self, filename: str, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__("Open", parent)
        self._filename = filename
        qconnect(self.clicked, lambda: self._open_file())

    def _open_file(self) -> None:
        if not (mw and mw.col):
            print("no collection available")
            return
        open_file(os.path.join(mw.col.media.dir(), self._filename))


class FileRenamePair(typing.NamedTuple):
    edit_widget: FileNameEdit
    open_button: FileOpenButton


def make_widget_pairs(edits: dict[str, FileNameEdit]) -> dict[str, FileRenamePair]:
    return {
        filename: FileRenamePair(edit_widget=edit, open_button=FileOpenButton(filename))
        for filename, edit in edits.items()
    }


class FileRenameLayout(QGridLayout):
    edits: dict[str, FileRenamePair]

    def __init__(self, edits: dict[str, FileNameEdit], parent: typing.Optional[QWidget] = None):
        super().__init__(parent)
        self.edits = make_widget_pairs(edits)
        self._init_ui()

    def _init_ui(self) -> None:
        for row_idx, column_idx, edit_widget in self._iter_widgets():
            # row: int, column: int, rowSpan: int, columnSpan: int
            self.addWidget(edit_widget, row_idx, column_idx)

    def _iter_widgets(self) -> Iterable[tuple[int, int, QWidget]]:
        for row_idx, filename in enumerate(self.edits):
            for column_idx, widget in enumerate(self.edits[filename]):
                yield row_idx, column_idx, widget


class RenameTask(typing.NamedTuple):
    old_filename: str
    new_filename: str


class MediaRenameDialog(QDialog):
    edits: dict[str, FileNameEdit]

    def __init__(self, editor: Editor, note: Note, filenames: list[str], *args, **kwargs):
        super().__init__(parent=editor.widget, *args, **kwargs)
        self.editor = editor
        self.edits = {filename: FileNameEdit(text=filename) for filename in filenames}
        self.note = note
        self.edits_layout = FileRenameLayout(self.edits)
        self.bottom_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        cast(QDialog, self).setWindowTitle(f"{ADDON_FULL_NAME}: rename files")
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self.setLayout(self._make_layout())
        self.connect_ui_elements()
        tweak_window(self)

    def _make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addLayout(self.edits_layout)
        layout.addWidget(self.bottom_box)
        return layout

    def connect_ui_elements(self):
        qconnect(self.bottom_box.accepted, self.accept)
        qconnect(self.bottom_box.rejected, self.reject)

    def to_rename(self) -> Iterable[RenameTask]:
        for old_filename, edit_widget in self.edits.items():
            if not edit_widget.valid:
                continue
            if old_filename != (new_filename := edit_widget.text()):
                yield RenameTask(old_filename, new_filename)

    def accept(self) -> None:
        if to_rename := list(self.to_rename()):
            rename_media_files(to_rename, self.note, self.editor)
        super().accept()


def rename_file(old_filename: str, new_filename: str) -> str:
    if not (mw and mw.col):
        print("no collection available")
        return old_filename
    print(f"{old_filename} => {new_filename}")
    with open(os.path.join(mw.col.media.dir(), old_filename), "rb") as f:
        return mw.col.media.write_data(new_filename, f.read())


def rename_media_files(to_rename: list[RenameTask], note: Note, parent: Editor):
    for old_filename, new_filename in to_rename:
        try:
            new_filename = rename_file(old_filename, new_filename)
        except FileNotFoundError:
            showCritical(f"{old_filename} doesn't exist.", title="Couldn't rename file.")
            continue
        for field_name, field_value in note.items():
            note[field_name] = field_value.replace(old_filename, new_filename)
    CollectionOp(parent=parent.widget, op=lambda col: col.update_note(note)).success(
        lambda out: tooltip(f"Renamed {len(to_rename)} files", parent=parent.parentWindow)
    ).run_in_background()

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import io
import re
import typing
from collections.abc import Iterable
from typing import Optional, cast

from anki.notes import Note
from aqt import mw
from aqt.editor import Editor
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import showCritical, tooltip

from .ajt_common.about_menu import tweak_window
from .ajt_common.monospace_line_edit import MonoSpaceLineEdit
from .ajt_common.utils import open_file
from .config import MediaConverterConfig, get_global_config
from .consts import ADDON_FULL_NAME, WINDOW_MIN_WIDTH
from .media_deduplication.deduplication import do_replacements


class FileNameEdit(MonoSpaceLineEdit):
    _edit_max_len = 119

    def __init__(self, text: str):
        super().__init__()
        self.setMaxLength(self._edit_max_len)
        self._valid = False
        qconnect(self.textChanged, self.validate)
        self.setText(text)

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
    def __init__(self, filename: str, parent: Optional[QWidget] = None) -> None:
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

    def __init__(self, edits: dict[str, FileNameEdit], parent: Optional[QWidget] = None):
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
    """Base rename dialog. Can be used without Anki running."""

    edits: dict[str, FileNameEdit]

    def __init__(self, filenames: list[str], parent: Optional[QWidget] = None):
        super().__init__(parent=parent)
        self.edits = {filename: FileNameEdit(text=filename) for filename in filenames}
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

    def can_rename_all_files(self) -> bool:
        """True if all rename line edits are valid."""
        return all(e.valid for e in self.edits.values())


class AnkiMediaRenameDialog(MediaRenameDialog):
    """Rename dialog that performs the actual rename inside Anki."""

    def __init__(self, editor: Editor, note: Note, filenames: list[str], cfg: Optional[MediaConverterConfig] = None):
        super().__init__(filenames, parent=editor.widget)
        self.editor = editor
        self.note = note
        self._cfg = cfg or get_global_config()

    def accept(self) -> None:
        if not self.can_rename_all_files():
            self.tooltip("Some file names are invalid.")
            return
        if to_rename := list(self.to_rename()):
            self._rename_media_files(to_rename, self.note, self.editor)
        super().accept()

    def tooltip(self, msg: str) -> None:
        tooltip(msg, parent=self.editor.parentWindow, period=self._cfg.tooltip_duration_milliseconds)

    def _rename_media_files(self, to_rename: list[RenameTask], note: Note, editor: Editor):
        to_rename = list(try_rename_files(to_rename))
        for old_filename, new_filename in to_rename:
            for field_name, field_value in note.items():
                note[field_name] = do_replacements(note[field_name], old_filename, new_filename)

        def on_success() -> None:
            self.tooltip(format_report_message(to_rename))

        CollectionOp(
            parent=editor.widget,
            op=lambda col: col.update_note(note),
        ).success(lambda out: on_success()).run_in_background()


def duplicate_file_in_collection(old_filename: str, new_filename: str) -> str:
    """Returns new filename after Anki possibly alters it."""
    if not (mw and mw.col):
        print("no collection available")
        return old_filename
    print(f"{old_filename} => {new_filename}")
    with open(os.path.join(mw.col.media.dir(), old_filename), "rb") as f:
        return mw.col.media.write_data(new_filename, f.read())


def format_report_message(to_rename: list[RenameTask]) -> str:
    buffer = io.StringIO()
    buffer.write(f"<p>Renamed <code>{len(to_rename)}</code> files.</p>")
    buffer.write("<ol>")
    for old_name, new_name in to_rename:
        buffer.write(f"<li><code>{old_name}</code> → <code>{new_name}</code></li>")
    buffer.write("</ol>")
    return buffer.getvalue()


def try_rename_files(to_rename: list[RenameTask]) -> Iterable[RenameTask]:
    """Yields successful renames."""
    for old_filename, new_filename in to_rename:
        try:
            new_filename = duplicate_file_in_collection(old_filename, new_filename)
        except FileNotFoundError:
            showCritical(f"{old_filename} doesn't exist.", title="Couldn't rename file.")
            continue
        yield RenameTask(old_filename=old_filename, new_filename=new_filename)

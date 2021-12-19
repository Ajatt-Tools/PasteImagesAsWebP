# Paste Images As WebP add-on for Anki 2.1
# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
from typing import List, Iterable, Tuple, Optional

from anki.notes import Note
from anki.utils import joinFields
from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.operations import CollectionOp
from aqt.qt import *
from aqt.utils import tooltip

from .ajt_common import tweak_window
from .consts import *


class FileNameEdit(QLineEdit):
    _edit_max_len = 119

    def __init__(self, text: str):
        super().__init__()
        self.setMaxLength(self._edit_max_len)
        self.setFont(QFont("Monospace", 11))
        self.setText(text)
        qconnect(self.textChanged, self.validate)
        self._valid = True

    @property
    def valid(self) -> bool:
        return self._valid

    def text(self):
        return super().text().strip('-_ ')

    def validate(self):
        self._valid = (
            len(self.text().encode('utf-8')) <= self._edit_max_len
            and re.match(r'^[^\[\]<>:\'"/|?*\\]+\.[\w]+$', self.text())
        )
        if self._valid:
            self.setStyleSheet("")
        else:
            self.setStyleSheet("background-color: #eb6b60;")


class MediaRenameDialog(QDialog):
    def __init__(self, editor: Editor, note: Note, filenames: List[str], *args, **kwargs):
        super().__init__(parent=editor.widget, *args, **kwargs)
        self.editor: Editor = editor
        self.edits = {filename: FileNameEdit(text=filename) for filename in filenames}
        self.note = note
        self.edits_layout = QVBoxLayout()
        self.bottom_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.setWindowTitle(f"{ADDON_NAME}: rename files")
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self.setLayout(self.make_layout())
        self.connect_ui_elements()
        tweak_window(self)

    def show(self) -> None:
        for widget in self.edits.values():
            self.edits_layout.addWidget(widget)
        super().show()

    def make_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addLayout(self.edits_layout)
        layout.addWidget(self.bottom_box)
        return layout

    def connect_ui_elements(self):
        qconnect(self.bottom_box.accepted, self.on_accept)
        qconnect(self.bottom_box.rejected, self.reject)

    def to_rename(self) -> Iterable[Tuple[str, str]]:
        widget: QLineEdit
        for old_filename, widget in self.edits.items():
            if old_filename != (new_filename := widget.text()):
                yield old_filename, new_filename

    def on_accept(self):
        return self.accept() if all(e.valid for e in self.edits.values()) else None

    def accept(self) -> None:
        super().accept()
        if to_rename := list(self.to_rename()):
            rename_media_files(to_rename, self.note, self.editor)


def find_sounds(html: str) -> List[str]:
    return re.findall(r'\[sound:([^\[\]]+)]', html)


def find_images(html: str) -> List[str]:
    return re.findall(r'<img[^<>]*src="([^<>\'"]+)"[^<>]*>', html)


def collect_media_filenames(html: str):
    return find_images(html) + find_sounds(html)


def rename_file(old_filename: str, new_filename: str) -> str:
    print(f"{old_filename} => {new_filename}")
    with open(os.path.join(mw.col.media.dir(), old_filename), 'rb') as f:
        return mw.col.media.write_data(new_filename, f.read())


def rename_media_files(to_rename: List[Tuple[str, str]], note: Note, parent: Editor):
    for old_filename, new_filename in to_rename:
        new_filename = rename_file(old_filename, new_filename)
        for field_name, field_value in note.items():
            note[field_name] = field_value.replace(old_filename, new_filename)
    CollectionOp(
        parent=parent.widget,
        op=lambda col: col.update_note(note)
    ).success(
        lambda out: tooltip(f"Renamed {len(to_rename)} files", parent=parent.parentWindow)
    ).run_in_background()


class Menus:
    """Holds a reference to MediaRenameDialog to avoid spawning the same window multiple times."""
    file_rename_dialog: Optional[MediaRenameDialog] = None

    @classmethod
    def del_ref(cls) -> None:
        cls.file_rename_dialog = None

    @classmethod
    def create_rename_dialog(cls, *args, **kwargs) -> MediaRenameDialog:
        d = cls.file_rename_dialog = MediaRenameDialog(*args, **kwargs)
        qconnect(d.finished, lambda result: cls.del_ref())
        return d

    @classmethod
    def show_rename_dialog(cls, editor: Editor) -> None:
        if cls.file_rename_dialog:
            return
        elif editor.note and (filenames := collect_media_filenames(joinFields(editor.note.fields))):
            cls.create_rename_dialog(editor, editor.note, filenames).show()

    @classmethod
    def add_editor_button(cls, buttons: List[str], editor: Editor) -> None:
        b = editor.addButton(
            icon=os.path.join(ADDON_PATH, "icons", "edit.svg"),
            cmd="rename_media_files",
            func=cls.show_rename_dialog,
            tip="Rename media files referenced by note.",
        )
        buttons.append(b)


def init():
    gui_hooks.editor_did_init_buttons.append(Menus.add_editor_button)

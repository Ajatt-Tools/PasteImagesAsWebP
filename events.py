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

import anki
import aqt.editor
from aqt import gui_hooks
from aqt import mw
from aqt.utils import KeyboardModifiersPressed

from gui import BulkConvertDialog
from .bulkconvert import convert_stored_image
from .common import *
from .config import config
from .webp import ShowOptions, ImageConverter, CanceledPaste, InvalidInput


def should_paste_raw():
    return KeyboardModifiersPressed().shift


def convert_mime(mime: QMimeData, editor: Editor, action: ShowOptions):
    w = ImageConverter(editor, action)
    try:
        w.convert(mime)
    except InvalidInput:
        pass
    except CanceledPaste as ex:
        tooltip(str(ex))
        mime = QMimeData()
    except RuntimeError as ex:
        tooltip(str(ex))
    except FileNotFoundError:
        tooltip("File not found.")
    else:
        mime = QMimeData()
        mime.setHtml(f'<img alt="webp image" src="{w.filename}">')
        result_tooltip(w.filepath)

    return mime


def on_process_mime(
        mime: QMimeData,
        editor_web_view: aqt.editor.EditorWebView,
        internal: bool,
        _extended: bool,
        drop_event: bool) -> QMimeData:
    if internal or should_paste_raw():
        return mime

    if config["drag_and_drop"] and drop_event:
        return convert_mime(mime, editor_web_view.editor, action=ShowOptions.drag_and_drop)

    if config["copy_paste"] and not drop_event and (mime.hasImage() or has_local_file(mime)):
        return convert_mime(mime, editor_web_view.editor, action=ShowOptions.menus)

    return mime


def convert_and_replace_stored_image(filename: str, note: anki.notes.Note):
    if new_filename := convert_stored_image(filename):
        for field_name, field_value in note.items():
            note[field_name] = field_value.replace(f'src="{filename}"', f'src="{new_filename}"')


def should_convert_images_in_new_note(note: anki.notes.Note) -> bool:
    """
    Convert images to WebP when a new note is added by AnkiConnect.
    Skip notes added using the Add dialog.
    """
    return (
            config['convert_on_note_add'] is True
            and mw.app.activeWindow() is None
            and note.id == 0
    )


class ConvertOnAddNote:
    def __init__(self):
        self._should_show_settings = (
                config["show_settings"] == ShowOptions.always
                or config["show_settings"] == ShowOptions.add_note
        )

    def _maybe_show_settings(self):
        if self._should_show_settings:
            dialog = BulkConvertDialog(mw)
            if not dialog.exec():
                raise CanceledPaste("Canceled convert dialog")
        self._should_show_settings = False

    def convert_note(self, note: anki.notes.Note):
        if (joined_fields := note.joined_fields()) and '<img' in joined_fields:
            for filename in find_convertible_images(joined_fields):
                if mw.col.media.have(filename):
                    print(f"Converting file: {filename}")
                    self._maybe_show_settings()
                    convert_and_replace_stored_image(filename, note)


def on_add_note(_self: anki.collection.Collection, note: anki.notes.Note, _deck_id: anki.decks.DeckId):
    if should_convert_images_in_new_note(note):
        print("Paste Images As WebP: detected an attempt to create a new note with images.")
        converter = ConvertOnAddNote()
        try:
            converter.convert_note(note)
        except CanceledPaste:
            tooltip("Canceled")


def init():
    gui_hooks.editor_will_process_mime.append(on_process_mime)
    anki.collection.Collection.add_note = anki.hooks.wrap(
        # TODO replace this call with a hook when a hook is available.
        old=anki.collection.Collection.add_note,
        new=on_add_note,
        pos='before',
    )

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import anki
import aqt.editor
from anki import hooks
from aqt import gui_hooks, mw
from aqt.utils import KeyboardModifiersPressed

from .common import *
from .config import config
from .image_conversion import CanceledPaste, InvalidInput, OnAddNoteConverter, OnPasteConverter, ShowOptions


def should_paste_raw():
    return KeyboardModifiersPressed().shift


def convert_mime(mime: QMimeData, editor: Editor, action: ShowOptions):
    w = OnPasteConverter(editor, editor.note, action)

    try:
        w.convert_mime(mime)
    except InvalidInput:
        pass
    except CanceledPaste as ex:
        w.tooltip(ex)
        mime = QMimeData()
    except FileNotFoundError:
        w.tooltip("File not found.")
    except (RuntimeError, AttributeError) as ex:
        w.tooltip(ex)
    else:
        mime = QMimeData()
        mime.setHtml(image_html(w.filename))
        w.result_tooltip(w.filepath)

    return mime


def on_process_mime(
    mime: QMimeData, editor_web_view: aqt.editor.EditorWebView, internal: bool, _extended: bool, drop_event: bool
) -> QMimeData:
    if internal or should_paste_raw():
        return mime

    if config["drag_and_drop"] and drop_event:
        return convert_mime(mime, editor_web_view.editor, action=ShowOptions.drag_and_drop)

    if config["copy_paste"] and not drop_event and (mime.hasImage() or has_local_file(mime)):
        return convert_mime(mime, editor_web_view.editor, action=ShowOptions.paste)

    return mime


def should_convert_images_in_new_note(note: anki.notes.Note) -> bool:
    """
    Convert media files when a new note is added by AnkiConnect.
    Skip notes added using the Add dialog.
    """
    return config["convert_on_note_add"] is True and mw.app.activeWindow() is None and note.id == 0


def on_add_note(_self: anki.collection.Collection, note: anki.notes.Note, _deck_id: anki.decks.DeckId) -> None:
    if should_convert_images_in_new_note(note):
        converter = OnAddNoteConverter(mw, note, action=ShowOptions.add_note)
        try:
            converter.convert_note()
        except CanceledPaste as ex:
            tooltip(str(ex), parent=mw)
        except (OSError, RuntimeError, FileNotFoundError):
            pass


def init():
    gui_hooks.editor_will_process_mime.append(on_process_mime)
    hooks.note_will_be_added.append(on_add_note)

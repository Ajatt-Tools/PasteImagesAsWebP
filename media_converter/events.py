# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import os.path

import anki
import aqt.editor
from anki import hooks
from anki.hooks import wrap
from anki.utils import tmpfile
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import KeyboardModifiersPressed

from .common import has_local_file, image_html, is_excluded_image_extension, tooltip
from .config import config
from .consts import ADDON_NAME_SNAKE
from .file_converters.file_converter import FFmpegNotFoundError
from .file_converters.image_converter import (
    CanceledPaste,
    ImageConverter,
    InvalidInput,
    ffmpeg_not_found_dialog,
)
from .file_converters.on_add_note_converter import OnAddNoteConverter
from .file_converters.on_paste_converter import OnPasteConverter
from .utils.show_options import ShowOptions


def should_paste_raw() -> bool:
    return KeyboardModifiersPressed().shift


def convert_mime(mime: QMimeData, editor: aqt.editor.Editor, action: ShowOptions):
    conv = OnPasteConverter(editor, action)

    try:
        new_file_path = conv.convert_mime(mime)
    except FFmpegNotFoundError:
        ffmpeg_not_found_dialog()
    except InvalidInput:
        pass
    except CanceledPaste as ex:
        conv.tooltip(ex)
        mime = QMimeData()
    except FileNotFoundError:
        conv.tooltip("File not found.")
    except (RuntimeError, AttributeError) as ex:
        conv.tooltip(ex)
    else:
        mime = QMimeData()
        mime.setHtml(image_html(os.path.basename(new_file_path)))
        conv.result_tooltip(new_file_path)
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
    assert mw
    return config["convert_on_note_add"] is True and mw.app.activeWindow() is None and note.id == 0


def on_add_note(_self: anki.collection.Collection, note: anki.notes.Note, _deck_id: anki.decks.DeckId) -> None:
    if should_convert_images_in_new_note(note):
        converter = OnAddNoteConverter(note, action=ShowOptions.add_note, parent=mw)
        try:
            converter.convert_note()
        except FFmpegNotFoundError:
            ffmpeg_not_found_dialog()
        except CanceledPaste as ex:
            tooltip(str(ex), parent=mw)
        except (OSError, RuntimeError, FileNotFoundError):
            pass


def on_setup_mask_editor(self: aqt.editor.Editor, image_path: str, _old: Callable) -> None:
    """
    Wrap Image Occlusion and convert the pasted image before Occlusion is used.
    https://docs.ankiweb.net/editing.html#image-occlusion
    """
    if config["copy_paste"] and not is_excluded_image_extension(os.path.basename(image_path)):
        conv = OnPasteConverter(self, action=ShowOptions.paste)
        try:
            image_path = conv.convert_image(image_path)
        except FFmpegNotFoundError:
            ffmpeg_not_found_dialog()
        except FileNotFoundError:
            conv.tooltip("File not found.")
        except Exception as ex:
            conv.tooltip(ex)
        else:
            conv.result_tooltip(image_path)
    return _old(self, image_path)


def init() -> None:
    gui_hooks.editor_will_process_mime.append(on_process_mime)
    hooks.note_will_be_added.append(on_add_note)
    aqt.editor.Editor.setup_mask_editor = wrap(aqt.editor.Editor.setup_mask_editor, on_setup_mask_editor, pos="around")

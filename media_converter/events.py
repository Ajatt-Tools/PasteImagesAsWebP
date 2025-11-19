# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import os.path

import anki
import aqt.editor
from anki import hooks
from anki.hooks import wrap
from aqt import gui_hooks, mw
from aqt.qt import *
from aqt.utils import KeyboardModifiersPressed, tooltip

from .common import has_local_file, image_html
from .config import MediaConverterConfig
from .file_converters.file_converter import FFmpegNotFoundError
from .file_converters.find_media import FindMedia
from .file_converters.image_converter import CanceledPaste, ffmpeg_not_found_dialog
from .file_converters.on_add_note_converter import OnAddNoteConverter
from .file_converters.on_paste_converter import TEMP_IMAGE_FORMAT, OnPasteConverter
from .utils.show_options import ShowOptions
from .utils.temp_file import TempFile


def should_paste_raw() -> bool:
    return KeyboardModifiersPressed().shift


class Events:
    _config: MediaConverterConfig
    _finder: FindMedia

    def __init__(self, config: MediaConverterConfig) -> None:
        self._config = config
        self._finder = FindMedia(config)

    def _convert_mime(self, mime: QMimeData, editor: aqt.editor.Editor, action: ShowOptions) -> QMimeData:
        conv = OnPasteConverter(editor, action, self._config)
        with TempFile(suffix=f".{TEMP_IMAGE_FORMAT}") as tmp_file:
            if to_convert := conv.mime_to_image_file(mime, tmp_file.path()):
                try:
                    new_file_path = conv.convert_mime(to_convert)
                except FFmpegNotFoundError:
                    ffmpeg_not_found_dialog()
                except CanceledPaste as ex:
                    conv.tooltip(ex)
                    # Treat "Cancel" as both "don't convert" and "don't paste". Erase mime data.
                    mime = QMimeData()
                except FileNotFoundError:
                    conv.tooltip("File not found.")
                except (RuntimeError, AttributeError) as ex:
                    conv.tooltip(ex)
                else:
                    # File has been converted.
                    mime = QMimeData()
                    mime.setHtml(image_html(os.path.basename(new_file_path)))
                    conv.result_tooltip(new_file_path)
        return mime

    def on_process_mime(
        self,
        mime: QMimeData,
        editor_web_view: aqt.editor.EditorWebView,
        internal: bool,
        _extended: bool,
        drop_event: bool,
    ) -> QMimeData:
        if internal or should_paste_raw():
            return mime

        if self._config.drag_and_drop and drop_event:
            return self._convert_mime(mime, editor_web_view.editor, action=ShowOptions.drag_and_drop)

        if self._config.copy_paste and not drop_event and (mime.hasImage() or has_local_file(mime)):
            return self._convert_mime(mime, editor_web_view.editor, action=ShowOptions.paste)

        return mime

    def _should_convert_images_in_new_note(self, note: anki.notes.Note) -> bool:
        """
        Convert media files when a new note is added by AnkiConnect.
        Skip notes added using the Add dialog.
        """
        assert mw
        return self._config.convert_on_note_add is True and mw.app.activeWindow() is None and note.id == 0

    def on_add_note(
        self, _self: anki.collection.Collection, note: anki.notes.Note, _deck_id: anki.decks.DeckId
    ) -> None:
        if self._should_convert_images_in_new_note(note):
            converter = OnAddNoteConverter(note, action=ShowOptions.add_note, parent=mw, config=self._config)
            try:
                converter.convert_note()
            except FFmpegNotFoundError:
                ffmpeg_not_found_dialog()
            except CanceledPaste as ex:
                tooltip(str(ex), period=self._config.tooltip_duration_milliseconds, parent=mw)
            except (OSError, RuntimeError, FileNotFoundError):
                pass

    def on_setup_mask_editor(self, editor: aqt.editor.Editor, image_path: str, _old: Callable) -> None:
        """
        Wrap Image Occlusion and convert the pasted image before Occlusion is used.
        https://docs.ankiweb.net/editing.html#image-occlusion
        """
        if self._config.copy_paste and not self._finder.is_excluded_image_extension(os.path.basename(image_path)):
            conv = OnPasteConverter(editor, action=ShowOptions.paste, config=self._config)
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
        return _old(editor, image_path)


def init() -> None:
    from .config import config

    mw._ajt__media_converter_events = events = Events(config)
    gui_hooks.editor_will_process_mime.append(events.on_process_mime)
    hooks.note_will_be_added.append(events.on_add_note)
    aqt.editor.Editor.setup_mask_editor = wrap(
        aqt.editor.Editor.setup_mask_editor,
        events.on_setup_mask_editor,
        pos="around",
    )

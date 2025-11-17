# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import Optional

from anki.notes import Note
from aqt import mw
from aqt.qt import *

from ..config import MediaConverterConfig
from ..dialogs.paste_image_dialog import AnkiPasteImageDialog
from ..utils.show_options import ImageDimensions, ShowOptions
from .common import LocalFile
from .find_media import FindMedia
from .image_converter import CanceledPaste
from .internal_file_converter import InternalFileConverter


class OnAddNoteConverter:
    """
    Converter used when a new note is added by AnkiConnect.
    """

    _settings_shown: bool
    _action: ShowOptions
    _note: Note
    _parent: Optional[QWidget] = None
    _config: MediaConverterConfig
    _finder: FindMedia

    def __init__(
        self, note: Note, action: ShowOptions, parent: Optional[QWidget], config: MediaConverterConfig
    ) -> None:
        self._settings_shown = False
        self._action = action
        self._note = note
        self._parent = parent
        self._config = config
        self._finder = FindMedia(config)

    def _should_show_settings(self) -> bool:
        if not self._settings_shown:
            self._settings_shown = True
            return self._config.should_show_settings(self._action)
        return False

    def _maybe_show_settings(self, dimensions: ImageDimensions) -> int:
        """If a note contains multiple images, show settings only once per note."""
        if self._should_show_settings():
            return AnkiPasteImageDialog(config=self._config, dimensions=dimensions, parent=self._parent).exec()
        return QDialog.DialogCode.Accepted

    def _convert_and_replace_stored_image(self, filename: str) -> None:
        conv = InternalFileConverter(file=LocalFile.image(filename), editor=None, note=self._note, config=self._config)
        ans = self._maybe_show_settings(conv.initial_dimensions)
        if ans == QDialog.DialogCode.Rejected:
            raise CanceledPaste("Cancelled.")
        conv.convert_internal()
        self._update_note_fields(filename, conv.new_filename)

    def convert_note(self):
        for filename in self._finder.find_convertible_images(self._note.joined_fields()):
            if mw.col.media.have(filename):
                print(f"Converting file: {filename}")
                self._convert_and_replace_stored_image(filename)
        # TODO handle audio files

    def _update_note_fields(self, old_filename: str, new_filename: str) -> None:
        for field_name, field_value in self._note.items():
            self._note[field_name] = field_value.replace(f'src="{old_filename}"', f'src="{new_filename}"')

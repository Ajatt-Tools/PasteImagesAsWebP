# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import Optional

from anki.notes import Note
from aqt import mw
from aqt.qt import *

from ..common import find_convertible_images
from ..gui import maybe_show_settings
from ..utils.show_options import ShowOptions
from .common import ImageDimensions, LocalFile, should_show_settings
from .image_converter import CanceledPaste
from .internal_file_converter import InternalFileConverter


class OnAddNoteConverter:
    """
    Converter used when a new note is added by AnkiConnect.
    """

    def __init__(self, note: Note, action: ShowOptions, parent: Optional[QWidget]) -> None:
        self._settings_shown = False
        self._action = action
        self._note = note
        self._parent = parent

    def _should_show_settings(self) -> bool:
        if self._settings_shown is False:
            self._settings_shown = True
            return should_show_settings(self._action)
        return False

    def _maybe_show_settings(self, dimensions: ImageDimensions) -> int:
        """If a note contains multiple images, show settings only once per note."""
        if self._settings_shown is False:
            self._settings_shown = True
            return maybe_show_settings(dimensions, parent=self._parent, action=self._action)
        return QDialog.DialogCode.Accepted

    def _convert_and_replace_stored_image(self, filename: str):
        conv = InternalFileConverter(file=LocalFile.image(filename), editor=None, note=self._note)
        ans = self._maybe_show_settings(conv.initial_dimensions)
        if ans == QDialog.DialogCode.Rejected:
            raise CanceledPaste("Cancelled.")
        conv.convert_internal()
        self._update_note_fields(filename, conv.new_filename)

    def convert_note(self):
        for filename in find_convertible_images(self._note.joined_fields()):
            if mw.col.media.have(filename):
                print(f"Converting file: {filename}")
                self._convert_and_replace_stored_image(filename)
        # TODO handle audio files

    def _update_note_fields(self, old_filename: str, new_filename: str):
        for field_name, field_value in self._note.items():
            self._note[field_name] = field_value.replace(f'src="{old_filename}"', f'src="{new_filename}"')

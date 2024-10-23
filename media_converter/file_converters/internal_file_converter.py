# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import os.path
from typing import Optional

import aqt.editor
from anki.notes import Note
from aqt import mw
from aqt.qt import *

from ..config import config
from ..utils.file_paths_factory import FilePathFactory
from .common import ConverterType, ImageDimensions, LocalFile
from .file_converter import FileConverter
from .image_converter import ImageConverter


def get_extension(file: LocalFile) -> str:
    if file.type == ConverterType.audio:
        return config.audio_extension
    return config.image_extension


class InternalFileConverter:
    """
    Converter used when converting an image or audio file already stored in the collection (e.g. bulk-convert).
    """

    _initial_file_path: str
    _destination_file_path: str
    _conversion_finished: bool
    _converter: FileConverter

    def __init__(self, editor: Optional[aqt.editor.Editor], file: LocalFile, note: Note):
        self._conversion_finished = False
        self._fpf = FilePathFactory(note=note, editor=editor)
        self._initial_file_path = os.path.join(self._dest_dir, file.file_name)
        self._destination_file_path = self._fpf.make_unique_filepath(
            self._dest_dir,
            file.file_name,
            extension=get_extension(file),
        )
        self._converter = FileConverter(self._initial_file_path, self._destination_file_path)

    @property
    def _dest_dir(self) -> str:
        assert mw
        return mw.col.media.dir()

    @property
    def new_file_path(self) -> str:
        if not self._conversion_finished:
            raise RuntimeError("Conversion wasn't performed.")
        return self._destination_file_path

    @property
    def new_filename(self) -> str:
        return os.path.basename(self.new_file_path)

    @property
    def file_type(self) -> ConverterType:
        return self._converter.mode

    def is_image(self) -> bool:
        return self.file_type == ConverterType.image

    @property
    def initial_dimensions(self) -> ImageDimensions:
        assert isinstance(self._converter, ImageConverter)
        return self._converter.initial_dimensions

    def convert_internal(self) -> None:
        self._converter.convert()
        self._conversion_finished = True

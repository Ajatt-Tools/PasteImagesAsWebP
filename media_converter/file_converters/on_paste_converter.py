# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import typing

import aqt.editor
from aqt.qt import *

from ..common import filesize_kib, is_excluded_image_extension, tooltip, maybe_show_settings
from ..config import config
from ..utils.file_paths_factory import FilePathFactory
from ..utils.mime_helper import image_candidates
from ..utils.show_options import ImageDimensions, ShowOptions
from .image_converter import (
    CanceledPaste,
    ImageConverter,
    MimeImageNotFound,
    fetch_filename,
)

TEMP_IMAGE_FORMAT = "png"


class ConverterPayload(typing.NamedTuple):
    tmp_path: str
    dimensions: ImageDimensions
    initial_filename: typing.Optional[str]


def save_image(mime: QMimeData, tmp_path: str) -> ConverterPayload:
    for image in image_candidates(mime):
        if image and image.save(tmp_path, TEMP_IMAGE_FORMAT) is True:
            return ConverterPayload(
                tmp_path=tmp_path,
                initial_filename=fetch_filename(mime),
                dimensions=ImageDimensions(image.width(), image.height()),
            )
    raise MimeImageNotFound("Not an image file.")


def mime_to_image_file(mime: QMimeData, destination_path: str) -> typing.Optional[ConverterPayload]:
    """
    Try to save image file. Return None if the file can't be saved or the file type is excluded by the user.
    """
    try:
        to_convert = save_image(mime, destination_path)
    except MimeImageNotFound:
        # Mime doesn't contain images or the images are not supported by Qt.
        return None
    if to_convert.initial_filename and is_excluded_image_extension(to_convert.initial_filename):
        # Skip files with excluded extensions.
        return None
    return to_convert


class OnPasteConverter:
    """
    Converter used when an image is pasted or dragged from outside.
    """

    _editor: aqt.editor.Editor
    _action: ShowOptions

    def __init__(self, editor: aqt.editor.Editor, action: ShowOptions) -> None:
        self._editor = editor
        self._action = action

    def _maybe_show_settings(self, dimensions: ImageDimensions) -> None:
        result = maybe_show_settings(dimensions, parent=self._editor.parentWindow, action=self._action)
        if result == QDialog.DialogCode.Rejected:
            raise CanceledPaste("Cancelled.")

    def convert_image(self, image_path: str) -> str:
        fpf = FilePathFactory(note=self._editor.note, editor=self._editor)
        destination_path = fpf.make_unique_filepath(
            dest_dir=self._dest_dir,
            original_filename=os.path.basename(image_path),
            extension=config.image_extension,
        )
        conv = ImageConverter(image_path, destination_path)
        self._maybe_show_settings(conv.initial_dimensions)
        conv.convert()
        return destination_path

    def convert_mime(self, to_convert: ConverterPayload) -> str:
        self._maybe_show_settings(to_convert.dimensions)
        fpf = FilePathFactory(note=self._editor.note, editor=self._editor)
        destination_path = fpf.make_unique_filepath(
            dest_dir=self._dest_dir,
            original_filename=to_convert.initial_filename,
            extension=config.image_extension,
        )
        conv = ImageConverter(to_convert.tmp_path, destination_path)
        conv.convert()
        return destination_path
        # TODO handle audio

    def tooltip(self, msg: Union[Exception, str]) -> None:
        return tooltip(str(msg), parent=self._editor.parentWindow)

    def result_tooltip(self, filepath: str) -> None:
        return self.tooltip(
            f"<strong>{os.path.basename(filepath)}</strong> added.<br>File size: {filesize_kib(filepath):.3f} KiB."
        )

    @property
    def _dest_dir(self) -> str:
        return self._editor.mw.col.media.dir()

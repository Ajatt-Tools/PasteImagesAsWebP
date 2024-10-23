# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import typing

import aqt.editor
from aqt.qt import *

from ..common import filesize_kib, tooltip
from ..config import config
from ..gui import maybe_show_settings
from ..utils.file_paths_factory import FilePathFactory
from ..utils.mime_helper import image_candidates
from ..utils.show_options import ShowOptions
from ..utils.temp_file import TempFile
from .common import ImageDimensions
from .image_converter import CanceledPaste, ImageConverter, InvalidInput, fetch_filename


class ConverterPayload(typing.NamedTuple):
    initial_filename: typing.Optional[str]
    dimensions: ImageDimensions


def save_image(mime: QMimeData, tmp_path: str) -> ConverterPayload:
    for image in image_candidates(mime):
        if image and image.save(tmp_path, "png") is True:
            dimensions = ImageDimensions(image.width(), image.height())
            initial_filename = fetch_filename(mime)
            break
    else:
        raise InvalidInput("Not an image file.")
    return ConverterPayload(initial_filename, dimensions)


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

    def convert_mime(self, mime: QMimeData) -> str:
        with TempFile() as tmp_file:
            to_convert = save_image(mime, tmp_file.path())
            self._maybe_show_settings(to_convert.dimensions)
            fpf = FilePathFactory(note=self._editor.note, editor=self._editor)
            dest_file_path = fpf.make_unique_filepath(
                self._dest_dir,
                to_convert.initial_filename,
                extension=config.image_extension,
            )
            conv = ImageConverter(tmp_file.path(), dest_file_path)
            conv.convert()
            return dest_file_path

    def tooltip(self, msg: Union[Exception, str]) -> None:
        return tooltip(str(msg), parent=self._editor.parentWindow)

    def result_tooltip(self, filepath: str) -> None:
        return self.tooltip(
            f"<strong>{os.path.basename(filepath)}</strong> added.<br>File size: {filesize_kib(filepath):.3f} KiB."
        )

    @property
    def _dest_dir(self) -> str:
        return self._editor.mw.col.media.dir()

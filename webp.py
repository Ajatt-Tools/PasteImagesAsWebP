# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
import subprocess
from typing import Any
from typing import AnyStr

from anki.notes import Note
from aqt import mw

from .ajt_common.utils import find_executable as find_executable_ajt
from .common import *
from .config import config
from .consts import SUPPORT_DIR
from .utils.file_paths_factory import FilePathFactory
from .utils.mime_helper import iter_files, image_candidates
from .utils.show_options import ShowOptions
from .utils.temp_file import TempFile

IS_MAC = sys.platform.startswith("darwin")
IS_WIN = sys.platform.startswith("win32")


class CanceledPaste(Warning):
    pass


class InvalidInput(Warning):
    pass


class ImageNotLoaded(Exception):
    pass


@functools.cache
def startup_info():
    if IS_WIN:
        # Prevents a console window from popping up on Windows
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        si = None
    return si


@functools.cache
def support_exe_suffix() -> str:
    """
    The mecab executable file in the "support" dir has a different suffix depending on the platform.
    """
    if IS_WIN:
        return ".exe"
    elif IS_MAC:
        return ".mac"
    else:
        return ".lin"


def get_bundled_executable(name: str) -> str:
    """
    Get path to executable in the bundled "support" folder.
    Used to provide 'cwebp' on computers where it is not installed system-wide or can't be found.
    """
    path_to_exe = os.path.join(SUPPORT_DIR, name) + support_exe_suffix()
    assert os.path.isfile(path_to_exe), f"{path_to_exe} doesn't exist. Can't recover."
    if not IS_WIN:
        os.chmod(path_to_exe, 0o755)
    return path_to_exe


@functools.cache
def find_cwebp_exe() -> str:
    # https://developers.google.com/speed/webp/download
    return find_executable_ajt("cwebp") or get_bundled_executable("cwebp")


def stringify_args(args: list[Any]) -> list[str]:
    return list(map(str, args))


def smaller_than_requested(image: ImageDimensions) -> bool:
    return 0 < image.width < config['image_width'] or 0 < image.height < config['image_height']


def fetch_filename(mime: QMimeData) -> Optional[str]:
    for file in iter_files(mime):
        if base := os.path.basename(file):
            return base


class WebPConverter:
    def __init__(
            self,
            parent: Union[QWidget, Editor],
            note: Note,
            action: Optional[ShowOptions] = None,
    ):
        self._parent = parent
        self._note = note
        self._action = action
        self._original_filename: Optional[str] = None
        self._filepath: Optional[AnyStr] = None
        self._dimensions: Optional[ImageDimensions] = None
        self._filepath_factory = FilePathFactory(self)

    @property
    def dest_dir(self) -> str:
        return mw.col.media.dir()

    @property
    def parent_window(self) -> QWidget:
        if isinstance(self._parent, QWidget):
            return self._parent
        if isinstance(self._parent, Editor):
            return self._parent.parentWindow
        raise RuntimeError("Invalid parent type.")

    @property
    def widget(self) -> Optional[QWidget]:
        return (
            self._parent.widget
            if isinstance(self._parent, Editor)
            else self._parent
        )

    @property
    def editor(self) -> Optional[Editor]:
        if isinstance(self._parent, Editor):
            return self._parent

    @property
    def note(self) -> Optional[Note]:
        if isinstance(self._note, Note):
            return self._note
        if isinstance(self._parent, Editor):
            return self._parent.note

    @property
    def filepath(self) -> str:
        if self._filepath:
            return self._filepath
        else:
            raise RuntimeError("File path hasn't been set.")

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    def _set_output_filepath(self) -> str:
        """
        Set and return a unique output file path, optionally based on the original name.
        If a file with this name exists in the collection, will append digits at the end of the new name.
        """
        self._filepath = self._filepath_factory.make_unique_filepath(
            self._original_filename if config['preserve_original_filenames'] else None
        )
        return self._filepath

    def _should_show_settings(self) -> bool:
        return bool(self._action in config.show_settings())

    def _maybe_show_settings(self) -> int:
        from .gui import PasteDialog

        if not self._dimensions:
            raise ImageNotLoaded("file wasn't loaded before converting")

        if self._should_show_settings() is True:
            dlg = PasteDialog(self.widget, image=self._dimensions)
            return dlg.exec()
        return QDialog.DialogCode.Accepted

    def _get_resize_args(self) -> list[Union[str, int]]:
        if config['avoid_upscaling'] and smaller_than_requested(self._dimensions):
            # skip resizing if the image is already smaller than the requested size
            return []

        if config['image_width'] == 0 and config['image_height'] == 0:
            # skip resizing if both width and height are set to 0
            return []

        return ['-resize', config['image_width'], config['image_height']]

    def _to_webp(self, source_path: AnyStr, destination_path: AnyStr) -> bool:
        args = [find_cwebp_exe(), source_path, '-o', destination_path, '-q', config.get('image_quality')]
        args.extend(config.get('cwebp_args', []))
        args.extend(self._get_resize_args())

        p = subprocess.Popen(
            stringify_args(args),
            shell=False,
            bufsize=-1,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            startupinfo=startup_info(),
            universal_newlines=True,
            encoding="utf8"
        )

        stdout, stderr = p.communicate()

        if p.wait() != 0:
            print(f"cwebp failed.")
            print(f"exit code = {p.returncode}")
            print(stdout)
            return False

        return True


class OnPasteConverter(WebPConverter):
    """
    Converter used when an image is pasted or dragged from outside.
    """

    def convert_mime(self, mime: QMimeData) -> None:
        with TempFile() as tmp_file:
            if self._save_image(tmp_file.path(), mime) is False:
                raise RuntimeError("Couldn't save the image.")

            if self._maybe_show_settings() == QDialog.DialogCode.Rejected:
                raise CanceledPaste("Cancelled.")

            if self._to_webp(tmp_file, self._set_output_filepath()) is False:
                raise RuntimeError("cwebp failed")

    def _save_image(self, tmp_path: str, mime: QMimeData) -> bool:
        for image in image_candidates(mime):
            if image and image.save(tmp_path, 'png') is True:
                self._dimensions = ImageDimensions(image.width(), image.height())
                self._original_filename = fetch_filename(mime)
                break
        else:
            raise InvalidInput("Not an image file.")

        return self._dimensions is not None

    def tooltip(self, msg: Union[Exception, str]) -> None:
        return tooltip(str(msg), parent=self.parent_window)

    def result_tooltip(self, filepath: str) -> None:
        return self.tooltip(
            f"<strong>{os.path.basename(filepath)}</strong> added.<br>"
            f"File size: {filesize_kib(filepath):.3f} KiB.",
        )


class InternalFileConverter(WebPConverter):
    """
    Converter used when converting an image already stored in the collection (e.g. bulk-convert).
    """

    def load_internal(self, filename: str) -> None:
        with open(os.path.join(self.dest_dir, filename), 'rb') as f:
            image = QImage.fromData(f.read())
        self._dimensions = ImageDimensions(image.width(), image.height())
        self._original_filename = filename

    def convert_internal(self) -> None:
        if not self._original_filename:
            raise ImageNotLoaded("file wasn't loaded before converting")
        if self._to_webp(os.path.join(self.dest_dir, self._original_filename), self._set_output_filepath()) is False:
            raise RuntimeError("cwebp failed")


class OnAddNoteConverter(InternalFileConverter):
    """
    Converter used when a new note is added by AnkiConnect.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._settings_shown = False

    def _should_show_settings(self) -> bool:
        """ If a note contains multiple images, show settings only once per note. """
        if self._settings_shown is False:
            self._settings_shown = True
            return super()._should_show_settings()
        return False

    def _convert_and_replace_stored_image(self, filename: str):
        self.load_internal(filename)
        if self._maybe_show_settings() == QDialog.DialogCode.Rejected:
            raise CanceledPaste("Cancelled.")
        self.convert_internal()
        if self.filename:
            for field_name, field_value in self._note.items():
                self._note[field_name] = field_value.replace(f'src="{filename}"', f'src="{self.filename}"')

    def convert_note(self):
        if (joined_fields := self._note.joined_fields()) and '<img' in joined_fields:
            print("Paste Images As WebP: detected an attempt to create a new note with images.")
            for filename in find_convertible_images(joined_fields):
                if mw.col.media.have(filename):
                    print(f"Converting file: {filename}")
                    self._convert_and_replace_stored_image(filename)


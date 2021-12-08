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

import subprocess
from distutils.spawn import find_executable
from typing import Optional, AnyStr, List, Any

from aqt import mw
from aqt.editor import Editor
from aqt.qt import *

from .file_paths_factory import FilePathFactory
from .gui import ShowOptions, PasteDialog, ImageDimensions
from .mime_helper import image_candidates, files
from .temp_file import TempFile
from ..config import config
from ..consts import ADDON_PATH, IMAGE_EXTENSIONS

is_mac = sys.platform.startswith("darwin")
is_win = sys.platform.startswith("win32")


class CanceledPaste(Warning):
    pass


class InvalidInput(Warning):
    pass


def image_like_filename(filename: str):
    return any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)


def find_cwebp():
    exe = find_executable('cwebp')
    if exe is None:
        # https://developers.google.com/speed/webp/download
        exe = os.path.join(ADDON_PATH, "support", "cwebp")
        if is_win:
            exe += ".exe"
        else:
            if is_mac:
                exe += '_macos'
            os.chmod(exe, 0o755)
    return exe


def stringify_args(args: List[Any]) -> List[str]:
    return [str(arg) for arg in args]


def smaller_than_requested(image: ImageDimensions) -> bool:
    return image.width < config['image_width'] or image.height < config['image_height']


def fetch_filename(mime: QMimeData) -> Optional[str]:
    for file in files(mime):
        if base := os.path.basename(file):
            return base


class ImageConverter:
    def __init__(self, editor: Editor = None, action: ShowOptions = None):
        self.editor = editor
        self.action = action
        self.dest_dir = mw.col.media.dir()
        self.original_filename: Optional[str] = None
        self.filepath: Optional[AnyStr] = None
        self.dimensions: Optional[ImageDimensions] = None
        self.filepath_factory = FilePathFactory(self.dest_dir, self.editor)

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    def load_internal(self, filename: str) -> None:
        with open(os.path.join(self.dest_dir, filename), 'rb') as f:
            image = QImage.fromData(f.read())
            self.dimensions = ImageDimensions(image.width(), image.height())

    def convert_internal(self, filename: str) -> None:
        self.filepath = self.filepath_factory.make_unique_filepath(filename)
        if self.to_webp(os.path.join(self.dest_dir, filename), self.filepath) is False:
            raise RuntimeError("cwebp failed")

    def should_show_settings(self) -> bool:
        return config.get("show_settings") == ShowOptions.always or config.get("show_settings") == self.action

    def decide_show_settings(self) -> int:
        if self.should_show_settings() is True:
            dlg = PasteDialog(self.editor.widget, self.dimensions)
            return dlg.exec_()
        return QDialog.Accepted

    def save_image(self, tmp_path: str, mime: QMimeData) -> bool:
        for image in image_candidates(mime):
            if image and image.save(tmp_path, 'png') is True:
                self.dimensions = ImageDimensions(image.width(), image.height())
                self.original_filename = fetch_filename(mime)
                break
        else:
            if any(not image_like_filename(url.fileName()) for url in mime.urls()):
                raise InvalidInput("Not an image file.")

        return self.dimensions is not None

    def get_resize_args(self) -> List[Union[str, int]]:
        if config['avoid_upscaling'] and smaller_than_requested(self.dimensions):
            # skip resizing if the image is already smaller than the requested size
            return []

        if config['image_width'] == 0 and config['image_height'] == 0:
            # skip resizing if both width and height are set to 0
            return []

        return ['-resize', config['image_width'], config['image_height']]

    def to_webp(self, source_path: AnyStr, destination_path: AnyStr) -> bool:
        args = [cwebp, source_path, '-o', destination_path, '-q', config.get('image_quality')]
        args.extend(config.get('cwebp_args', []))
        args.extend(self.get_resize_args())

        p = subprocess.Popen(stringify_args(args),
                             shell=False,
                             bufsize=-1,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             startupinfo=si)
        stdout = p.communicate()[0]
        if p.wait() != 0:
            print(f"cwebp failed.")
            print(f"exit code = {p.returncode}")
            print(stdout)
            return False

        return True

    def set_output_filepath(self) -> str:
        self.filepath = self.filepath_factory.make_unique_filepath(
            self.original_filename if config['preserve_original_filenames'] else None
        )
        return self.filepath

    def convert(self, mime: QMimeData) -> None:
        with TempFile() as tmp_file:
            if self.save_image(tmp_file.path(), mime) is False:
                raise RuntimeError("Couldn't save the image.")

            if self.decide_show_settings() == QDialog.Rejected:
                raise CanceledPaste("Cancelled.")

            if self.to_webp(tmp_file, self.set_output_filepath()) is False:
                raise RuntimeError("cwebp failed")


cwebp = find_cwebp()

if is_win:
    # Prevents a console window from popping up on Windows
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    si = None

# -*- coding: utf-8 -*-

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

import random
import subprocess
import time
from distutils.spawn import find_executable
from pathlib import Path
from typing import Optional, NamedTuple

from aqt import mw
from aqt.qt import *

from .gui import ShowOptions, PasteDialog, ImageDimensions
from .mime_helper import image_candidates
from .tempfile import TempFile
from ..config import config
from ..consts import ADDON_PATH


def find_cwebp():
    exe = find_executable('cwebp')
    if exe is None:
        # https://developers.google.com/speed/webp/download
        support_dir = "support"
        if isWin:
            exe = os.path.join(ADDON_PATH, support_dir, "cwebp.exe")
        else:
            exe = os.path.join(ADDON_PATH, support_dir, "cwebp")
            os.chmod(exe, 0o755)
    return exe


def construct_filename(target_dir_path: str):
    """Returns a unique (filename, filepath) for the new webp image"""

    def new_filename() -> str:
        return f"paste_{int(time.time())}{random.randint(100, 999)}.webp"

    def make_full_path(name) -> str:
        return os.path.join(target_dir_path, name)

    out_filename: str = new_filename()
    while os.path.isfile(make_full_path(out_filename)):
        out_filename = new_filename()

    return Path(make_full_path(out_filename))


def stringify_args(args: list) -> list:
    return [str(arg) for arg in args]


def smaller_than_requested(image: QImage) -> bool:
    return image.width() < config['image_width'] or image.height() < config['image_height']


class Caller(NamedTuple):
    widget: QWidget
    action: ShowOptions


class ImageConverter:
    def __init__(self, caller: Caller):
        self.dest_dir = mw.col.media.dir()
        self.caller = caller
        self.filepath: Optional[Path] = None
        self.image: Optional[QImage] = None

    def shouldShowSettings(self) -> bool:
        return config.get("show_settings") == ShowOptions.always or config.get("show_settings") == self.caller.action

    def decideShowSettings(self) -> int:
        if self.shouldShowSettings() is True:
            dlg = PasteDialog(self.caller.widget, ImageDimensions(self.image.width(), self.image.height()))
            return dlg.exec_()
        return QDialog.Accepted

    def saveImage(self, tmp_path: str, mime: QMimeData) -> bool:
        for image in image_candidates(mime):
            if image and image.save(tmp_path, 'png') is True:
                self.image = image
                break
        else:
            return False

        return True

    def getResizeArgs(self):
        if config['avoid_upscaling'] and smaller_than_requested(self.image):
            # skip resizing if the image is already smaller than the requested size
            return []

        if config['image_width'] == 0 and config['image_height'] == 0:
            # skip resizing if both width and height are set to 0
            return []

        return ['-resize', config['image_width'], config['image_height']]

    def toWebP(self, source_path: os.PathLike, destination_path: os.PathLike) -> bool:
        args = [cwebp, source_path, '-o', destination_path, '-q', config.get('image_quality')]
        args.extend(config.get('cwebp_args', []))
        args.extend(self.getResizeArgs())

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

    def convert(self, mime: QMimeData) -> None:
        with TempFile() as tmp_file:
            if self.saveImage(tmp_file.path(), mime) is False:
                raise RuntimeError("Couldn't save the image.")

            if self.decideShowSettings() == QDialog.Rejected:
                raise Warning("Canceled.")

            webp_filepath: Path = construct_filename(self.dest_dir)

            if self.toWebP(tmp_file, webp_filepath) is False:
                raise RuntimeError("cwebp failed")

        self.filepath = webp_filepath


cwebp = find_cwebp()

if isWin:
    # Prevents a console window from popping up on Windows
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    si = None

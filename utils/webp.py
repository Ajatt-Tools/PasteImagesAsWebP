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
import itertools
import random
import re
import subprocess
import time
import unicodedata
from distutils.spawn import find_executable
from functools import wraps
from pathlib import Path
from time import gmtime, strftime
from typing import Optional, AnyStr

from aqt import mw
from aqt.editor import Editor
from aqt.qt import *

from .gui import ShowOptions, PasteDialog, ImageDimensions
from .mime_helper import image_candidates
from .temp_file import TempFile
from ..config import config
from ..consts import ADDON_PATH, IMAGE_EXTENSIONS


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
        if isWin:
            exe += ".exe"
        else:
            if isMac:
                exe += '_macos'
            os.chmod(exe, 0o755)
    return exe


def stringify_args(args: list) -> list:
    return [str(arg) for arg in args]


def smaller_than_requested(image: ImageDimensions) -> bool:
    return image.width < config['image_width'] or image.height < config['image_height']


def compatible_filename(f):
    max_len = 50

    def replace_forbidden_chars(s: str) -> str:
        return re.sub(r'[<>:"/|?*\\]+', '_', s, flags=re.MULTILINE | re.IGNORECASE)

    @wraps(f)
    def wrapper(*args, **kwargs) -> str:
        s = unicodedata.normalize('NFC', f(*args, **kwargs))
        s = replace_forbidden_chars(s)
        s = s.lower()
        return s[:max_len] if s else FilePathFactory.default_prefix

    return wrapper


class FilePathFactory:
    ext = '.webp'
    default_prefix = 'paste'

    def __init__(self, target_dir_path: str = None, editor: Editor = None):
        self.target_dir_path = target_dir_path
        self.editor = editor

        self.prefixes = {
            self.default_prefix: lambda: self.default_prefix,
            'sort-field': self.sort_field,
            'current-field': self.current_field,
        }
        self.suffixes = {
            'time-number': lambda: str(int(time.time() * 1000)),
            'time-human': lambda: strftime("%d-%b-%Y_%H:%M:%S", gmtime()),
        }

        self.patterns = [f'{prefix}_{suffix}{self.ext}' for prefix in self.prefixes for suffix in self.suffixes]

    def make_filename(self, pattern_id: int) -> str:
        try:
            pattern = self.patterns[pattern_id]
        except IndexError:
            pattern = self.patterns[0]

        for k, v in itertools.chain(self.prefixes.items(), self.suffixes.items()):
            pattern = pattern.replace(k, v())

        return pattern

    def make_unique_filepath(self) -> AnyStr:
        out_filename = self.make_filename(config.get('filename_pattern_num', 0))
        out_filename = self.ensure_unique(out_filename)
        return os.path.join(self.target_dir_path, out_filename)

    def ensure_unique(self, file_path: str) -> str:
        out = file_path
        cut = file_path[:-len(self.ext)]
        while os.path.isfile(out):
            out = cut + '_' + str(random.randint(100, 999)) + self.ext
        return out

    @compatible_filename
    def sort_field(self):
        try:
            sort_field = self.editor.note.note_type()['sortf']
            return self.editor.note.values()[sort_field]
        except AttributeError:
            return self.default_prefix

    @compatible_filename
    def current_field(self):
        try:
            return self.editor.note.values()[self.editor.currentField]
        except (AttributeError, TypeError):
            return self.default_prefix


class ImageConverter(object):
    def __init__(self, editor: Editor = None, action: ShowOptions = None):
        self.editor = editor
        self.action = action
        self.dest_dir = mw.col.media.dir()
        self.filepath: Optional[AnyStr] = None
        self.image: Optional[ImageDimensions] = None
        self.fp_fac = FilePathFactory(self.dest_dir, self.editor)

    @property
    def filename(self):
        return os.path.basename(self.filepath)

    def load_internal(self, filename: str):
        with open(os.path.join(self.dest_dir, filename), 'rb') as f:
            image = QImage.fromData(f.read())
            self.image = ImageDimensions(image.width(), image.height())

    def convert_internal(self, filename: str):
        source_filepath = os.path.join(self.dest_dir, filename)
        webp_filepath = self.fp_fac.ensure_unique(os.path.splitext(source_filepath)[0] + self.fp_fac.ext)

        if self.to_webp(source_filepath, webp_filepath) is False:
            raise RuntimeError("cwebp failed")

        self.filepath = webp_filepath

    def should_show_settings(self) -> bool:
        return config.get("show_settings") == ShowOptions.always or config.get("show_settings") == self.action

    def decide_show_settings(self) -> int:
        if self.should_show_settings() is True:
            dlg = PasteDialog(self.editor.widget, self.image)
            return dlg.exec_()
        return QDialog.Accepted

    def save_image(self, tmp_path: str, mime: QMimeData) -> bool:
        for image in image_candidates(mime):
            if image and image.save(tmp_path, 'png') is True:
                self.image = ImageDimensions(image.width(), image.height())
                break
        else:
            if any(not image_like_filename(url.fileName()) for url in mime.urls()):
                raise InvalidInput("Not an image file.")

            return False

        return True

    def get_resize_args(self):
        if config['avoid_upscaling'] and smaller_than_requested(self.image):
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

    def convert(self, mime: QMimeData) -> None:
        with TempFile() as tmp_file:
            if self.save_image(tmp_file.path(), mime) is False:
                raise RuntimeError("Couldn't save the image.")

            if self.decide_show_settings() == QDialog.Rejected:
                raise CanceledPaste("Cancelled.")

            webp_filepath = self.fp_fac.make_unique_filepath()

            if self.to_webp(tmp_file, webp_filepath) is False:
                raise RuntimeError("cwebp failed")

        self.filepath = webp_filepath


cwebp = find_cwebp()

if isWin:
    # Prevents a console window from popping up on Windows
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    si = None

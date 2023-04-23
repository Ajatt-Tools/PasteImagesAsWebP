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

import functools
import itertools
import random
import time
import unicodedata
from time import gmtime, strftime
from typing import AnyStr, Optional

from anki.utils import htmlToTextLine

from .image_converter import ImageConverter
from ..common import *
from ..config import config


def compatible_filename(f: Callable[..., str]):
    max_len_bytes = 90

    def replace_forbidden_chars(s: str) -> str:
        return re.sub(r'[\[\]<>:"/|?*\\;,&\']+', ' ', s, flags=re.MULTILINE | re.IGNORECASE)

    def sub_spaces(s: str) -> str:
        return re.sub(r' +', ' ', s)

    @functools.wraps(f)
    def wrapper(*args, **kwargs) -> str:
        s = f(*args, **kwargs)
        s = htmlToTextLine(s)
        s = s.encode('utf-8')[:max_len_bytes].decode('utf-8', errors='ignore')
        s = unicodedata.normalize('NFC', s)
        s = replace_forbidden_chars(s)
        s = s.lower()
        s = sub_spaces(s)
        s = s.strip('-_ ')
        return s if s else FilePathFactory.default_prefix

    return wrapper


def ensure_unique(file_path: str) -> str:
    name, ext = os.path.splitext(file_path)
    while os.path.isfile(file_path):
        file_path = name + '_' + str(random.randint(0, 9999)).zfill(4) + ext
    return file_path


class FilePathFactory:
    ext = '.webp'
    default_prefix = 'paste'

    def __init__(self, converter: Optional[ImageConverter] = None):
        self._converter = converter
        self._prefixes = {
            self.default_prefix: lambda: self.default_prefix,
            'sort-field': self._sort_field,
            'custom-field': self._custom_field,
            'current-field': self._current_field,
        }
        self._suffixes = {
            'time-number': lambda: str(int(time.time() * 1000)),
            'time-human': lambda: strftime("%d-%b-%Y_%H-%M-%S", gmtime()),
        }
        self._patterns = [
            f'{prefix}_{suffix}'
            for prefix in self._prefixes
            for suffix in self._suffixes
        ]

    @property
    def patterns_populated(self) -> Iterable[str]:
        return (self._apply_pattern(pattern) for pattern in self._patterns)

    def make_unique_filepath(self, original_filename: Optional[str]) -> AnyStr:
        return ensure_unique(os.path.join(
            self._converter.dest_dir,
            self._make_filename_no_ext(original_filename) + self.ext,
        ))

    @compatible_filename
    def _make_filename_no_ext(self, original_filename: Optional[str]):
        if original_filename:
            return os.path.splitext(original_filename)[0]
        else:
            def get_pattern() -> str:
                try:
                    return self._patterns[config['filename_pattern_num']]
                except IndexError:
                    return self._patterns[0]

            return self._apply_pattern(get_pattern())

    def _sort_field(self) -> str:
        try:
            sort_field = self._converter.note.note_type()['sortf']
            return self._converter.note.values()[sort_field]
        except AttributeError:
            return 'sort field'

    def _custom_field(self) -> str:
        try:
            return self._converter.note[config['custom_name_field']]
        except AttributeError:
            return 'custom field'
        except (TypeError, KeyError):
            return self._sort_field()

    def _current_field(self) -> str:
        try:
            return self._converter.note.values()[self._converter.editor.currentField]
        except (AttributeError, TypeError):
            # AttributeError is raised when editor is None
            # TypeError is raised when current field is None
            return 'current field'

    def _apply_pattern(self, pattern: str) -> str:
        for k, v in itertools.chain(self._prefixes.items(), self._suffixes.items()):
            pattern = pattern.replace(k, v())
        return pattern

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
import itertools
import random
import time
import unicodedata
from time import gmtime, strftime
from typing import AnyStr

from anki.notes import Note
from anki.utils import html_to_text_line

from ..common import *
from ..config import config
from .converter_interfaces import FileNamePatterns, ImageConverter


def compatible_filename(f: Callable[..., str]):
    max_len_bytes = 90

    def replace_forbidden_chars(s: str) -> str:
        return re.sub(r'[\[\]<>:"/|?*\\;,&\']+', " ", s, flags=re.MULTILINE | re.IGNORECASE)

    def sub_spaces(s: str) -> str:
        return re.sub(r" +", " ", s)

    @functools.wraps(f)
    def wrapper(*args, **kwargs) -> str:
        s = f(*args, **kwargs)
        s = html_to_text_line(s)
        s = s.encode("utf-8")[:max_len_bytes].decode("utf-8", errors="ignore")
        s = unicodedata.normalize("NFC", s)
        s = replace_forbidden_chars(s)
        s = s.lower()
        s = sub_spaces(s)
        s = s.strip("-_ ")
        return s or "file"

    return wrapper


def ensure_unique(file_path: str) -> str:
    name, ext = os.path.splitext(file_path)
    while os.path.isfile(file_path):
        file_path = name + "_" + str(random.randint(0, 9999)).zfill(4) + ext
    return file_path


def note_sort_field_content(note: Note) -> str:
    return note.values()[note.note_type()["sortf"]]


class FilePathFactory(FileNamePatterns):
    def __init__(self, converter: Optional[ImageConverter] = None):
        super().__init__()
        self._converter = converter

    def make_unique_filepath(self, original_filename: Optional[str]) -> AnyStr:
        return ensure_unique(
            os.path.join(
                self._converter.dest_dir,
                self._make_filename_no_ext(original_filename) + config.image_extension,
            )
        )

    @compatible_filename
    def _make_filename_no_ext(self, original_filename: Optional[str]):
        if original_filename:
            return os.path.splitext(original_filename)[0]
        else:

            def get_pattern() -> str:
                try:
                    return self._patterns[config["filename_pattern_num"]]
                except IndexError:
                    return self._patterns[0]

            return self._apply_pattern(get_pattern())

    def _apply_pattern(self, pattern: str) -> str:
        for k, v in itertools.chain(self._prefixes.items(), self._suffixes.items()):
            pattern = pattern.replace(k, v())
        return pattern

    def _sort_field(self) -> str:
        try:
            return note_sort_field_content(self._converter.note)
        except (AttributeError, TypeError, KeyError):
            return "image"

    def _custom_field(self) -> str:
        try:
            return self._converter.note[config["custom_name_field"]]
        except (AttributeError, TypeError, KeyError):
            return self._sort_field()

    def _current_field(self) -> str:
        try:
            return self._converter.note.values()[self._converter.editor.currentField]
        except (AttributeError, TypeError, KeyError):
            return self._sort_field()

    @staticmethod
    def _time_number():
        return str(int(time.time() * 1000))

    @staticmethod
    def _time_human():
        return strftime("%d-%b-%Y_%H-%M-%S", gmtime())

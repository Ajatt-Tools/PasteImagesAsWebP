# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
import itertools
import os
import random
import re
import time
import unicodedata
from time import gmtime, strftime
from typing import Callable, Optional

from anki.notes import Note
from anki.utils import html_to_text_line
from aqt.editor import Editor

from ..config import config
from .converter_interfaces import FileNamePatterns


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
    _note: Optional[Note]
    _editor: Optional[Editor]

    def __init__(self, note: Optional[Note], editor: Optional[Editor]) -> None:
        super().__init__()
        self._note = note
        self._editor = editor

    def make_unique_filepath(self, dest_dir: str, original_filename: Optional[str]) -> str:
        return ensure_unique(
            os.path.join(dest_dir, self._make_filename_no_ext(original_filename) + config.image_extension)
        )

    @compatible_filename
    def _make_filename_no_ext(self, original_filename: Optional[str]) -> str:
        if original_filename and config.preserve_original_filenames:
            return os.path.splitext(original_filename)[0]

        def get_pattern() -> str:
            try:
                return self._patterns[config["filename_pattern_num"]]
            except IndexError:
                return self._patterns[0]

        return self._apply_pattern(get_pattern())

    def _apply_pattern(self, pattern: str) -> str:
        for keyword, replace_fn in itertools.chain(self._prefixes.items(), self._suffixes.items()):
            pattern = pattern.replace(keyword, replace_fn())
        return pattern

    def _sort_field(self) -> str:
        if self._note:
            try:
                return note_sort_field_content(self._note)
            except (AttributeError, TypeError, KeyError):
                pass
        return "image"

    def _custom_field(self) -> str:
        if self._note:
            try:
                return self._note[config["custom_name_field"]]
            except (AttributeError, TypeError, KeyError):
                pass
        return self._sort_field()

    def _current_field(self) -> str:
        if self._note and self._editor and self._editor.currentField is not None:
            try:
                return self._note.values()[self._editor.currentField]
            except (AttributeError, TypeError, KeyError):
                pass
        return self._sort_field()

    @staticmethod
    def _time_number():
        return str(int(time.time() * 1000))

    @staticmethod
    def _time_human():
        return strftime("%d-%b-%Y_%H-%M-%S", gmtime())

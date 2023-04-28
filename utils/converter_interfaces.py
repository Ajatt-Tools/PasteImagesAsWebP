# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import abc
from typing import Protocol, Optional, Iterable

from anki.notes import Note
from aqt.editor import Editor


class ImageConverter(Protocol):
    @property
    @abc.abstractmethod
    def dest_dir(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def editor(self) -> Optional[Editor]:
        ...

    @property
    @abc.abstractmethod
    def note(self) -> Optional[Note]:
        ...


class FileNamePatterns:
    def __init__(self):
        self._prefixes = {
            'paste': self._default_prefix,
            'sort-field': self._sort_field,
            'custom-field': self._custom_field,
            'current-field': self._current_field,
        }
        self._suffixes = {
            'time-number': self._time_number,
            'time-human': self._time_human,
        }
        self._patterns = [
            f'{prefix}_{suffix}'
            for prefix in self._prefixes
            for suffix in self._suffixes
        ]

    def all_examples(self) -> Iterable[str]:
        return self._patterns

    @staticmethod
    def _default_prefix():
        return 'paste'

    @staticmethod
    def _sort_field() -> str:
        return 'sort-field'

    @staticmethod
    def _custom_field() -> str:
        return 'custom-field'

    @staticmethod
    def _current_field() -> str:
        return 'current-field'

    @staticmethod
    def _time_number():
        return 'epoch-time'

    @staticmethod
    def _time_human():
        return 'date-time'

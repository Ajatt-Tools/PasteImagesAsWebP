# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Callable, Iterable


class FileNamePatterns:
    _prefixes: dict[str, Callable[[], str]]
    _suffixes: dict[str, Callable[[], str]]
    _patterns: list[str]

    def __init__(self) -> None:
        self._prefixes = {
            "paste": self._default_prefix,
            "sort-field": self._sort_field,
            "custom-field": self._custom_field,
            "current-field": self._current_field,
        }
        self._suffixes = {
            "time-number": self._time_number,
            "time-human": self._time_human,
        }
        self._patterns = [f"{prefix}_{suffix}" for prefix in self._prefixes for suffix in self._suffixes]

    def all_examples(self) -> Iterable[str]:
        return self._patterns

    @staticmethod
    def _default_prefix() -> str:
        return "paste"

    @staticmethod
    def _sort_field() -> str:
        return "sort-field"

    @staticmethod
    def _custom_field() -> str:
        return "custom-field"

    @staticmethod
    def _current_field() -> str:
        return "current-field"

    @staticmethod
    def _time_number() -> str:
        return "epoch-time"

    @staticmethod
    def _time_human() -> str:
        return "date-time"

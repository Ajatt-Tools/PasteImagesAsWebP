# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import Optional

from .common import LocalFile


class ConvertResult:
    def __init__(self) -> None:
        self._converted: dict[LocalFile, str] = {}
        self._failed: dict[LocalFile, Optional[Exception]] = {}

    def add_converted(self, old_file: LocalFile, new_filename: str) -> None:
        self._converted[old_file] = new_filename

    def add_failed(self, file: LocalFile, exception: Optional[Exception] = None):
        self._failed[file] = exception

    @property
    def converted(self) -> dict[LocalFile, str]:
        return self._converted

    @property
    def failed(self) -> dict[LocalFile, Optional[Exception]]:
        return self._failed

    def is_dirty(self) -> bool:
        return bool(self._converted or self._failed)

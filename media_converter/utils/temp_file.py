# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import os
from tempfile import mkstemp


class TempFileException(Exception):
    pass


class TempFile(os.PathLike):
    """A simple class for automatic management of temp file paths"""

    _tmp_filepath: str = ""
    _fd: int = 0
    _opened: bool = False

    def __init__(self, suffix: str = ".png"):
        self._fd, self._tmp_filepath = mkstemp(prefix="ajt__", suffix=suffix)
        self._opened = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace_back):
        self.close()

    def __del__(self):
        self.close()

    def __fspath__(self) -> str:
        return self.path()

    def __repr__(self) -> str:
        return self.path()

    def __str__(self) -> str:
        return self.path()

    def path(self) -> str:
        if not (self._opened and self._tmp_filepath):
            raise TempFileException("error creating temp file")
        return self._tmp_filepath

    def close(self):
        if self._opened:
            os.close(self._fd)
            os.remove(self._tmp_filepath)
            self._opened = False

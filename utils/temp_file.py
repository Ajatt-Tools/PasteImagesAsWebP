# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import os
from tempfile import mkstemp


class TempFile(os.PathLike):
    """A simple class for automatic management of temp file paths"""

    def __init__(self):
        self.fd, self.tmp_filepath = mkstemp()
        self.opened = True

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
        if len(self.tmp_filepath) < 1:
            raise Exception()
        return self.tmp_filepath

    def close(self):
        if self.opened is True:
            os.close(self.fd)
            os.remove(self.tmp_filepath)
            self.opened = False

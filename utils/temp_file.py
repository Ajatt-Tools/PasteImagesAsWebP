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
            raise Exception
        return self.tmp_filepath

    def close(self):
        if self.opened is True:
            os.close(self.fd)
            os.remove(self.tmp_filepath)
            self.opened = False

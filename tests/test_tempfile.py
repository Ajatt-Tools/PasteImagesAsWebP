# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os.path

import pytest

from media_converter.utils.temp_file import TempFile, TempFileException


def test_temp_file() -> None:
    with TempFile() as tmp_file:
        path = tmp_file.path()
        assert path.endswith(".png")
        assert os.path.isfile(path)
        assert os.path.getsize(path) == 0
    # should have been deleted.
    with pytest.raises(TempFileException):
        tmp_file.path()
    assert not os.path.isfile(path)

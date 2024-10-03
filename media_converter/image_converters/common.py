# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import subprocess
import sys
from typing import Any, NamedTuple

from ..config import config
from ..utils.show_options import ShowOptions

IS_MAC = sys.platform.startswith("darwin")
IS_WIN = sys.platform.startswith("win32")


class ImageDimensions(NamedTuple):
    width: int
    height: int


def should_show_settings(action: ShowOptions) -> bool:
    return bool(action in config.show_settings())


@functools.cache
def startup_info():
    if IS_WIN:
        # Prevents a console window from popping up on Windows
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    else:
        si = None
    return si


def stringify_args(args: list[Any]) -> list[str]:
    return [str(arg) for arg in args]


def create_process(args: list[Any]):
    return subprocess.Popen(
        stringify_args(args),
        shell=False,
        bufsize=-1,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        startupinfo=startup_info(),
        universal_newlines=True,
        encoding="utf8",
    )

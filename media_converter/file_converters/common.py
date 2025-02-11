# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import enum
import functools
import subprocess
import sys
import typing
from typing import Any

IS_MAC = sys.platform.startswith("darwin")
IS_WIN = sys.platform.startswith("win32")
COMMON_AUDIO_FORMATS = frozenset(
    (".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".aiff", ".amr", ".ape", ".mp2", ".oga", ".oma", ".opus")
)


class ConverterType(enum.Enum):
    audio = "audio"
    image = "image"


class LocalFile(typing.NamedTuple):
    file_name: str
    type: ConverterType

    @classmethod
    def image(cls, file_name: str):
        return cls(file_name, ConverterType.image)

    @classmethod
    def audio(cls, file_name: str):
        return cls(file_name, ConverterType.audio)


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


def create_process(args: list[Any]) -> subprocess.Popen:
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


def run_process(p: subprocess.Popen) -> None:
    stdout, stderr = p.communicate()
    if p.wait() != 0:
        print("Conversion failed.")
        print(f"exit code = {p.returncode}")
        print(stdout)
        raise RuntimeError(f"Conversion failed with code {p.returncode}.")

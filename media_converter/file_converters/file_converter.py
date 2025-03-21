# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from typing import Optional

from ..ajt_common.utils import find_executable as find_executable_ajt
from .common import COMMON_AUDIO_FORMATS, ConverterType, get_file_extension


class FFmpegNotFoundError(FileNotFoundError):
    pass


def is_audio_file(filename: str) -> bool:
    return get_file_extension(filename) in COMMON_AUDIO_FORMATS


@functools.cache
def find_ffmpeg_exe() -> Optional[str]:
    # https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
    return find_executable_ajt("ffmpeg")


class FileConverter:
    """
    Base class for the image and audio converters.
    """

    _subclasses_map: dict[ConverterType, type["FileConverter"]] = {}  # audio -> AudioConverter
    _mode: ConverterType  # used to mark subclasses

    def __init_subclass__(cls, **kwargs) -> None:
        # mode is one of ("audio", "image")
        mode = kwargs.pop("mode")  # suppresses ide warning
        super().__init_subclass__(**kwargs)
        cls._subclasses_map[mode] = cls
        cls._mode = mode

    def __new__(cls, source_path: str, destination_path: str) -> "FileConverter":
        if is_audio_file(source_path):
            mode = ConverterType.audio
        else:
            mode = ConverterType.image
        obj = object.__new__(cls._subclasses_map[mode])
        assert obj.mode == mode, f"{obj.mode} should be equal to {mode}"
        return obj

    @property
    def mode(self) -> ConverterType:
        return self._mode

    def convert(self) -> None:
        raise NotImplementedError()

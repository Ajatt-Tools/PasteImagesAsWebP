# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import enum
from typing import Sequence


@enum.unique
class ImageFormat(enum.Enum):
    webp = enum.auto()
    avif = enum.auto()


SUPPORTED_IMAGE_FORMATS: Sequence[str] = tuple(x.name for x in ImageFormat)


@enum.unique
class AudioContainer(enum.Enum):
    opus = "opus"
    ogg = "ogg"

    @classmethod
    def _missing_(cls, _value):
        return cls.ogg

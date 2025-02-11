# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import enum
from collections.abc import Iterable, Sequence
from typing import Union

from aqt import mw

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .ajt_common.utils import clamp
from .utils.show_options import ShowOptions
from .widgets.audio_slider_box import MAX_AUDIO_BITRATE_K, MIN_AUDIO_BITRATE_K


@enum.unique
class ImageFormat(enum.Enum):
    webp = enum.auto()
    avif = enum.auto()


@enum.unique
class AudioContainer(enum.Enum):
    opus = "opus"
    ogg = "ogg"

    @classmethod
    def _missing_(cls, _value):
        return cls.ogg


def cfg_comma_sep_str_to_file_ext_set(cfg_str: str) -> set[str]:
    """
    Take a string containing a comma-separated list of file formats
    and convert it into a set of file extensions
    """
    return {f".{ext}".lower().strip() for ext in cfg_str.split(",")}


class MediaConverterConfig(AddonConfigManager):

    def __init__(self, default: bool = False) -> None:
        super().__init__(default)

    def show_settings(self) -> Sequence[ShowOptions]:
        instances = []
        for name in self["show_settings"].split(","):
            try:
                instances.append(ShowOptions[name])
            except KeyError:
                continue
        return instances

    def set_show_options(self, options: Iterable[ShowOptions]):
        self["show_settings"] = ",".join(option.name for option in options)

    @property
    def image_format(self) -> ImageFormat:
        return ImageFormat[self["image_format"].lower()]

    @property
    def audio_container(self) -> AudioContainer:
        return AudioContainer(self["audio_container"].lower())

    @property
    def image_extension(self) -> str:
        return f".{self.image_format.name}".lower()

    @property
    def audio_extension(self) -> str:
        return f".{self.audio_container.name}".lower()

    @property
    def bulk_reconvert(self) -> bool:
        return self["bulk_reconvert"]

    @bulk_reconvert.setter
    def bulk_reconvert(self, value: bool) -> None:
        self["bulk_reconvert"] = value

    @property
    def image_quality(self) -> int:
        return clamp(min_val=0, val=self["image_quality"], max_val=100)

    @property
    def image_width(self) -> int:
        return clamp(min_val=0, val=self["image_width"], max_val=99_999)

    @property
    def image_height(self) -> int:
        return clamp(min_val=0, val=self["image_height"], max_val=99_999)

    @property
    def preserve_original_filenames(self) -> bool:
        return self["preserve_original_filenames"]

    @property
    def convert_on_note_add(self) -> bool:
        return self["convert_on_note_add"]

    def get_excluded_image_extensions(self, include_converted: bool) -> frozenset[str]:
        """
        Return excluded formats and prepend a dot to each format.
        If the "reconvert" option is enabled when using bulk-convert,
        the target extension (.avif or .webp) is not excluded.

        :param include_converted: The current image extension will not be in the list,
               thus webp/avif files will be reconverted.
        :return: Image extensions.
        """
        excluded_extensions = cfg_comma_sep_str_to_file_ext_set(self["excluded_image_containers"])
        if include_converted:
            excluded_extensions.discard(self.image_extension)
        else:
            excluded_extensions.add(self.image_extension)
        return frozenset(excluded_extensions)

    def get_excluded_audio_extensions(self, include_converted: bool) -> frozenset[str]:
        """
        Return excluded formats and prepend a dot to each format.
        If the "reconvert" option is enabled when using bulk-convert,
        the target extension (.opus or .ogg) is not excluded.

        :param include_converted: The current audio extension will not be in the list,
               thus ogg/opus files will be reconverted.
        :return: Audio extensions.
        """
        excluded_extensions = cfg_comma_sep_str_to_file_ext_set(self["excluded_audio_containers"])
        if include_converted:
            excluded_extensions.discard(self.audio_extension)
        else:
            excluded_extensions.add(self.audio_extension)
        return frozenset(excluded_extensions)

    @property
    def enable_image_conversion(self) -> bool:
        return bool(self["enable_image_conversion"])

    @property
    def enable_audio_conversion(self) -> bool:
        return bool(self["enable_audio_conversion"])

    @property
    def ffmpeg_audio_args(self) -> list[Union[str, int]]:
        return self["ffmpeg_audio_args"]

    @property
    def audio_bitrate_k(self) -> int:
        return clamp(MIN_AUDIO_BITRATE_K, self["ffmpeg_audio_bitrate"], MAX_AUDIO_BITRATE_K)

    @audio_bitrate_k.setter
    def audio_bitrate_k(self, kbit_s: int) -> None:
        self["ffmpeg_audio_bitrate"] = kbit_s

    @property
    def tooltip_duration_seconds(self) -> int:
        return int(self["tooltip_duration_seconds"])

    @property
    def drag_and_drop(self) -> bool:
        return bool(self["drag_and_drop"])

    @property
    def copy_paste(self) -> bool:
        return bool(self["copy_paste"])

    def should_show_settings(self, action: ShowOptions) -> bool:
        return bool(action in self.show_settings())


def get_global_config() -> MediaConverterConfig:
    assert mw, "anki must be running"
    return config


if mw:
    config = MediaConverterConfig()
    set_config_update_action(config.update_from_addon_manager)

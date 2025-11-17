# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from collections.abc import Iterable, Sequence
from typing import Union

from aqt import mw

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .ajt_common.utils import clamp
from .utils.config_types import SUPPORTED_IMAGE_FORMATS, AudioContainer, ImageFormat
from .utils.show_options import ShowOptions
from .widgets.audio_slider_box import MAX_AUDIO_BITRATE_K, MIN_AUDIO_BITRATE_K


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

    @image_format.setter
    def image_format(self, image_format: Union[ImageFormat, str]) -> None:
        if isinstance(image_format, str):
            assert image_format in SUPPORTED_IMAGE_FORMATS, "image format should be supported."
            self["image_format"] = image_format.lower()
        elif isinstance(image_format, ImageFormat):
            self["image_format"] = image_format.name.lower()
        else:
            raise ValueError(f"invalid type passed: {type(image_format)}")

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
        assert isinstance(value, bool), "value should be bool"
        self["bulk_reconvert"] = bool(value)

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
        return bool(self["convert_on_note_add"])

    @property
    def show_editor_button(self) -> bool:
        return bool(self["show_editor_button"])

    @property
    def delete_original_file_on_convert(self) -> bool:
        return self["delete_original_file_on_convert"]

    @property
    def filename_pattern_num(self) -> int:
        """
        Index in list FileNamePatterns
        """
        return int(self["filename_pattern_num"])

    @filename_pattern_num.setter
    def filename_pattern_num(self, filename_pattern_num: int) -> None:
        """
        Index in list FileNamePatterns
        """
        assert isinstance(filename_pattern_num, int), "filename_pattern_num should be int"
        self["filename_pattern_num"] = int(filename_pattern_num)

    def get_excluded_image_extensions(self, include_converted: bool) -> frozenset[str]:
        """
        Return excluded formats and prepend a dot to each format.
        If the "reconvert" option is enabled when using bulk-convert,
        the target extension (.avif or .webp) is not excluded.

        :param include_converted: The current image extension will not be in the list,
               thus webp/avif files will be reconverted.
        :return: Image extensions.
        """
        excluded_extensions = cfg_comma_sep_str_to_file_ext_set(self.excluded_image_containers)
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
        excluded_extensions = cfg_comma_sep_str_to_file_ext_set(self.excluded_audio_containers)
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
    def cwebp_args(self) -> list[Union[str, int]]:
        return self["cwebp_args"]

    @property
    def ffmpeg_args(self) -> list[Union[str, int]]:
        return self["ffmpeg_args"]

    @property
    def ffmpeg_audio_args(self) -> list[Union[str, int]]:
        return self["ffmpeg_audio_args"]

    @property
    def audio_bitrate_k(self) -> int:
        return clamp(MIN_AUDIO_BITRATE_K, self["ffmpeg_audio_bitrate"], MAX_AUDIO_BITRATE_K)

    @audio_bitrate_k.setter
    def audio_bitrate_k(self, kbit_s: int) -> None:
        assert isinstance(kbit_s, int), "kbit/s should be int"
        self["ffmpeg_audio_bitrate"] = int(kbit_s)

    @property
    def tooltip_duration_seconds(self) -> int:
        return int(self["tooltip_duration_seconds"])

    @property
    def tooltip_duration_millisecond(self) -> int:
        return self.tooltip_duration_seconds * 1_000

    @property
    def drag_and_drop(self) -> bool:
        return bool(self["drag_and_drop"])

    @property
    def copy_paste(self) -> bool:
        return bool(self["copy_paste"])

    @property
    def excluded_image_containers(self) -> str:
        return self["excluded_image_containers"]

    @excluded_image_containers.setter
    def excluded_image_containers(self, value: str) -> None:
        assert isinstance(value, str), "value should be a string"
        self["excluded_image_containers"] = str(value)

    @property
    def excluded_audio_containers(self) -> str:
        return self["excluded_audio_containers"]

    @excluded_audio_containers.setter
    def excluded_audio_containers(self, value: str) -> None:
        assert isinstance(value, str), "value should be a string"
        self["excluded_audio_containers"] = str(value)

    @property
    def shortcut(self) -> str:
        return self["shortcut"]

    @property
    def custom_name_field(self) -> str:
        return self["custom_name_field"]

    @custom_name_field.setter
    def custom_name_field(self, custom_name_field: str) -> None:
        assert isinstance(custom_name_field, str), "custom_name_field should be a string"
        self["custom_name_field"] = str(custom_name_field)

    @property
    def avoid_upscaling(self) -> bool:
        return bool(self["avoid_upscaling"])

    def should_show_settings(self, action: ShowOptions) -> bool:
        return bool(action in self.show_settings())

    @property
    def show_context_menu_entry(self) -> bool:
        return bool(self["show_context_menu_entry"])


def get_global_config() -> MediaConverterConfig:
    assert mw, "anki must be running"
    return config


if mw:
    config = MediaConverterConfig()
    set_config_update_action(config.update_from_addon_manager)

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import enum
from collections.abc import Iterable, Sequence

from aqt import mw

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .ajt_common.utils import clamp
from .utils.show_options import ShowOptions


@enum.unique
class ImageFormat(enum.Enum):
    webp = enum.auto()
    avif = enum.auto()


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
    def image_extension(self) -> str:
        return f".{self.image_format.name}"

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
        """
        excluded_extensions = cfg_comma_sep_str_to_file_ext_set(self["excluded_image_formats"])
        if include_converted:
            excluded_extensions.discard(self.image_extension)
        return frozenset(excluded_extensions)


if mw:
    config = MediaConverterConfig()
    set_config_update_action(config.update_from_addon_manager)

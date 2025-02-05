# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import enum
from collections.abc import Iterable, Sequence

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .ajt_common.utils import clamp
from .utils.show_options import ShowOptions


@enum.unique
class ImageFormat(enum.Enum):
    webp = enum.auto()
    avif = enum.auto()


class MediaConverterConfig(AddonConfigManager):
    def __init__(self, default: bool = False) -> None:
        super().__init__(default)
        set_config_update_action(self.update_from_addon_manager)

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
    
    @property
    def delete_original_file_on_convert(self) -> bool:
        return self["delete_original_file_on_convert"]


config = MediaConverterConfig()

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import NamedTuple

from ..config import config
from ..utils.show_options import ShowOptions


class ImageDimensions(NamedTuple):
    width: int
    height: int


def should_show_settings(action: ShowOptions) -> bool:
    return bool(action in config.show_settings())

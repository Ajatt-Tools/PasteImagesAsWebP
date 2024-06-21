# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os

from .ajt_common.consts import ADDON_SERIES

ADDON_PATH = os.path.dirname(os.path.abspath(__file__))
ADDON_NAME = f"{ADDON_SERIES} Media Converter"
THIS_ADDON_MODULE = __name__.split(".")[0]
SUPPORT_DIR = os.path.join(ADDON_PATH, "support")

WINDOW_MIN_WIDTH = 400

REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Anki)"}
REQUEST_TIMEOUTS = (3.05, 12.05)

assert os.path.isdir(SUPPORT_DIR), "support dir must exist."

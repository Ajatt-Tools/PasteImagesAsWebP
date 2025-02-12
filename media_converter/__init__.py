# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import sys

from aqt import mw


def start_addon() -> None:
    from . import bulkconvert, events, media_rename, menus

    bulkconvert.init()
    menus.init()
    events.init()
    media_rename.init()


if mw and "pytest" not in sys.modules:
    start_addon()

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


try:
    # https://github.com/beartype/beartype
    from beartype.claw import beartype_this_package

    beartype_this_package()
except ImportError:
    print("Note: beartype is disabled in this session.")
    pass

import sys

from aqt import mw


def start_addon() -> None:
    from . import bulkconvert, events, menus

    bulkconvert.init()
    menus.init()
    events.init()


if mw and "pytest" not in sys.modules:
    start_addon()

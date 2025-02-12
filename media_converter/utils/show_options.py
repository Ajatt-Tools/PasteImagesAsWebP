# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import enum
from typing import NamedTuple


class ShowOptions(enum.Enum):
    toolbar = "Toolbar"
    drag_and_drop = "On drag and drop"
    add_note = "Note added"
    paste = "On paste"


class ImageDimensions(NamedTuple):
    width: int
    height: int


def main():
    print(ShowOptions["toolbar"])


if __name__ == "__main__":
    main()

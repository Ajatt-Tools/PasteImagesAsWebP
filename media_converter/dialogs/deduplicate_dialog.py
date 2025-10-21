# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import typing
from typing import Sequence

from aqt.qt import QDialogButtonBox

from ..ajt_common.stats_table_dialog import StatsDialog
from ..ajt_common.utils import ui_translate


class DeduplicateTableColumns(typing.NamedTuple):
    duplicate_name: str
    original_name: str

    @classmethod
    def column_names(cls) -> Sequence[str]:
        return [ui_translate(field) for field in cls.__annotations__]


class DeduplicateMediaConfirmDialog(StatsDialog):
    name: str = "ajt__deduplicate_media_confirm_dialog"
    win_title: str = "Deduplicate media files"
    button_box_buttons: QDialogButtonBox.StandardButton = (
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )

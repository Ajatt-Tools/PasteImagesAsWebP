# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import itertools
from collections.abc import Iterable
from typing import Optional, cast

from anki.notes import Note
from aqt.qt import *

from .config import config
from .consts import ADDON_FULL_NAME, WINDOW_MIN_WIDTH
from .dialogs.settings_dialog_base import ADDON_NAME_SNAKE, AnkiSaveAndRestoreGeomDialog
from .file_converters.common import ImageDimensions, should_show_settings
from .utils.show_options import ShowOptions
from .widgets.image_slider_box import ImageSliderBox
from .widgets.presets_editor import PresetsEditor


class SettingsDialog(AnkiSaveAndRestoreGeomDialog):
    name: str = f"ajt__{ADDON_NAME_SNAKE}_options_dialog"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        cast(QDialog, self).setWindowTitle(ADDON_FULL_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self._sliders = ImageSliderBox()
        self._presets_editor = PresetsEditor("Presets", sliders=self._sliders)
        self._main_vbox = QVBoxLayout()
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

    def setup_ui(self) -> None:
        self.setLayout(self.create_main_layout())
        self.populate_main_vbox()
        self.setup_logic()
        self.set_initial_values()

    def exec(self) -> int:
        self.setup_ui()
        return super().exec()

    def create_main_layout(self) -> QLayout:
        layout = QVBoxLayout()
        layout.addLayout(self._main_vbox)
        layout.addStretch()
        layout.addWidget(self._button_box)
        return layout

    def populate_main_vbox(self) -> None:
        self._main_vbox.addWidget(self._sliders)
        self._main_vbox.addWidget(self._presets_editor)

    def setup_logic(self) -> None:
        qconnect(self._button_box.accepted, self.accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def set_initial_values(self) -> None:
        self._sliders.set_limits(config["max_image_width"], config["max_image_height"])
        self._sliders.image_width = config.image_width
        self._sliders.image_height = config.image_height
        self._sliders.image_quality = config.image_quality
        self._presets_editor.set_items(config["saved_presets"])

    def accept(self) -> None:
        config.update(self._sliders.as_dict())
        config["saved_presets"] = self._presets_editor.as_list()
        config.write_config()
        return super().accept()


def get_all_keys(notes: Iterable[Note]) -> list[str]:
    """
    Returns a list of field names present in passed notes, without duplicates.
    """
    return sorted(frozenset(itertools.chain(*(note.keys() for note in notes))))


class PasteDialog(SettingsDialog):
    """Dialog shown on paste."""

    def __init__(self, dimensions: ImageDimensions, parent=None) -> None:
        self._dimensions = dimensions
        super().__init__(parent)

    def populate_main_vbox(self) -> None:
        super().populate_main_vbox()
        self._main_vbox.addWidget(self.create_scale_settings_group_box())

    def create_scale_settings_group_box(self) -> QGroupBox:
        gbox = QGroupBox(f"Original size: {self._dimensions.width} x {self._dimensions.height} px")
        gbox.setLayout(self.create_scale_options_grid())
        return gbox

    def adjust_sliders(self, factor: float) -> None:
        if self._sliders.image_width > 0:
            self._sliders.image_width = int(self._dimensions.width * factor)
        if self._sliders.image_height > 0:
            self._sliders.image_height = int(self._dimensions.height * factor)

    def create_scale_options_grid(self) -> QGridLayout:
        grid = QGridLayout()
        factors = (1 / 8, 1 / 4, 1 / 2, 1, 1.5, 2)
        columns = 3
        for index, factor in enumerate(factors):
            i = int(index / columns)
            j = index - (i * columns)
            button = QPushButton(f"{factor}x")
            qconnect(button.clicked, lambda _, f=factor: self.adjust_sliders(f))
            grid.addWidget(button, i, j)
        return grid


def maybe_show_settings(dimensions: ImageDimensions, parent: Optional[QWidget], action: ShowOptions) -> int:
    if should_show_settings(action):
        dlg = PasteDialog(dimensions=dimensions, parent=parent)
        return dlg.exec()
    return QDialog.DialogCode.Accepted

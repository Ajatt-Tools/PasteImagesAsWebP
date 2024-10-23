# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import typing

from aqt.qt import *

from .image_slider_box import ImageSliderBox


class PresetDict(typing.TypedDict):
    image_height: int
    image_quality: int
    image_width: int


def preset_to_str(preset: PresetDict) -> str:
    return f"{preset['image_width']}x{preset['image_height']} @ {preset['image_quality']}"


class PresetsEditor(QGroupBox):
    def __init__(self, name: str, sliders: ImageSliderBox) -> None:
        super().__init__(name)
        self._sliders = sliders
        self.combo = QComboBox()
        self.add_current = QPushButton("Add current")
        self.remove_selected = QPushButton("Remove selected")
        self.apply_selected = QPushButton("Apply selected")
        self.setLayout(self.create_layout())
        self.connect_buttons()

    def create_layout(self) -> QLayout:
        layout = QGridLayout()
        layout.addWidget(self.combo, 0, 0, 1, 3)  # row, col, row-span, col-span
        layout.addWidget(self.add_current, 1, 0)
        layout.addWidget(self.remove_selected, 1, 1)
        layout.addWidget(self.apply_selected, 1, 2)
        return layout

    def as_list(self) -> list[PresetDict]:
        return [self.combo.itemData(index) for index in range(self.combo.count())]

    def add_items(self, items: list[PresetDict]) -> None:
        for item in items:
            self.combo.addItem(preset_to_str(item), item)

    def set_items(self, items: list[PresetDict]) -> None:
        """
        Remove all previously added items and add new items.
        """
        self.combo.clear()
        self.add_items(items)

    def add_new_preset(self) -> None:
        self.combo.addItem(preset_to_str(preset := self._sliders.as_dict()), preset)

    def apply_selected_preset(self) -> None:
        data: PresetDict
        if data := self.combo.currentData():
            self._sliders.image_width = data["image_width"]
            self._sliders.image_height = data["image_height"]
            self._sliders.image_quality = data["image_quality"]

    def connect_buttons(self) -> None:
        qconnect(self.add_current.clicked, self.add_new_preset)
        qconnect(self.remove_selected.clicked, lambda: self.combo.removeItem(self.combo.currentIndex()))
        qconnect(self.apply_selected.clicked, self.apply_selected_preset)

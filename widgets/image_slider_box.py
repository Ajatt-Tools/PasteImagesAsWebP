# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Dict

from aqt.qt import *

from .rich_slider import RichSlider


class ImageSliderBox(QGroupBox):
    def __init__(self, *args, max_width: int = 1000, max_height: int = 1000, **kwargs):
        super().__init__(*args, **kwargs)  # type: ignore
        self._width = RichSlider("Width", "px", limit=max_width)
        self._height = RichSlider("Height", "px", limit=max_height)
        self._quality = RichSlider("Quality", "%", limit=100)
        self.setLayout(self.create_layout())
        self.set_tooltips()

    def _map(self):
        return zip(
            ('image_width', 'image_height', 'image_quality',),
            (self._width, self._height, self._quality,),
        )

    def set_limits(self, width: int, height: int):
        self._width.set_limit(width)
        self._height.set_limit(height)

    def as_dict(self) -> dict[str, int]:
        return {key: slider.value for key, slider in self._map()}

    @property
    def quality(self) -> int:
        return self._quality.value

    @property
    def width(self) -> int:
        return self._width.value

    @width.setter
    def width(self, value: int):
        self._width.value = value

    @property
    def height(self) -> int:
        return self._height.value

    @height.setter
    def height(self, value: int):
        self._height.value = value

    def create_layout(self) -> QLayout:
        grid = QGridLayout()
        for y_index, slider in enumerate((self._width, self._height, self._quality)):
            grid.addWidget(QLabel(slider.title), y_index, 0)
            for x_index, widget in enumerate(slider.widgets):
                grid.addWidget(widget, y_index, x_index + 1)
        return grid

    def populate(self, config: dict[str, int]):
        for key, slider in self._map():
            slider.value = config.get(key)

    def set_tooltips(self):
        side_tooltip = str(
            "Desired %s.\n"
            "If either of the width or height parameters is 0,\n"
            "the value will be calculated preserving the aspect-ratio.\n"
            "If both values are 0, no resizing is performed (not recommended)."
        )
        quality_tooltip = str(
            "Specify the compression factor between 0 and 100.\n"
            "A small factor produces a smaller file with lower quality.\n"
            "Best quality is achieved by using a value of 100."
        )
        self._width.set_tooltip(side_tooltip % 'width')
        self._height.set_tooltip(side_tooltip % 'height')
        self._quality.set_tooltip(quality_tooltip)

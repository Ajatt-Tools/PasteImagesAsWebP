# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from collections.abc import Iterable
from typing import NamedTuple

from aqt.qt import *

from .rich_slider import RichSlider


class Sliders(NamedTuple):
    image_width: RichSlider
    image_height: RichSlider
    image_quality: RichSlider


def sliders_to_grid(sliders: Iterable[RichSlider]) -> QLayout:
    grid = QGridLayout()
    slider: RichSlider
    for y_index, slider in enumerate(sliders):
        grid.addWidget(QLabel(slider.title), y_index, 0)
        for x_index, widget in enumerate(slider.widgets, start=1):
            grid.addWidget(widget, y_index, x_index)
    return grid


class ImageSliderBox(QWidget):
    def __init__(self, max_width: int = 1000, max_height: int = 1000) -> None:
        super().__init__()
        self._sliders = Sliders(
            image_width=RichSlider("Width", "px", upper_limit=max_width),
            image_height=RichSlider("Height", "px", upper_limit=max_height),
            image_quality=RichSlider("Quality", "%", upper_limit=100),
        )
        self._setup_ui()
        self.set_tooltips()

    def _setup_ui(self) -> None:
        layout = sliders_to_grid(self._sliders)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def set_limits(self, width: int, height: int) -> None:
        self._sliders.image_width.set_upper_limit(width)
        self._sliders.image_height.set_upper_limit(height)

    def as_dict(self) -> dict[str, int]:
        return {key: slider.value for key, slider in self._sliders._asdict().items()}

    @property
    def image_width(self) -> int:
        return self._sliders.image_width.value

    @image_width.setter
    def image_width(self, value: int):
        self._sliders.image_width.value = value

    @property
    def image_height(self) -> int:
        return self._sliders.image_height.value

    @image_height.setter
    def image_height(self, value: int):
        self._sliders.image_height.value = value

    @property
    def image_quality(self) -> int:
        return self._sliders.image_quality.value

    @image_quality.setter
    def image_quality(self, value: int):
        self._sliders.image_quality.value = value

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
        self._sliders.image_width.set_tooltip(side_tooltip % "width")
        self._sliders.image_height.set_tooltip(side_tooltip % "height")
        self._sliders.image_quality.set_tooltip(quality_tooltip)

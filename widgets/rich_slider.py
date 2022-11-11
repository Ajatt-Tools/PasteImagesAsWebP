# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Tuple

from aqt.qt import *


class RichSlider:
    """
    This class acts like a struct holding a slider and a spinbox together.
    The two widgets are connected so that any change to one are reflected on the other.
    """

    SLIDER_STEP = 5

    def __init__(self, title: str, unit: str = "px", limit: int = 100, step: int = SLIDER_STEP):
        self.title = title
        self.slider = QSlider(Qt.Horizontal)
        self.spinbox = QSpinBox()
        self.unitLabel = QLabel(unit)
        qconnect(self.slider.valueChanged, self.spinbox.setValue)
        qconnect(self.spinbox.valueChanged, self.slider.setValue)
        self._set_step(step)
        self.set_limit(limit)

    def set_limit(self, limit: int):
        """
        Set the maximum value the user is allowed to apply.
        """
        return self._set_range(0, limit)

    def set_tooltip(self, tooltip: str):
        self.slider.setToolTip(tooltip)

    @property
    def widgets(self) -> Tuple[QWidget, ...]:
        return self.slider, self.spinbox, self.unitLabel

    @property
    def value(self) -> int:
        return self.slider.value()

    @value.setter
    def value(self, value: int):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def _set_range(self, start: int, stop: int):
        self.slider.setRange(start, stop)
        self.spinbox.setRange(start, stop)

    def _set_step(self, step: int):
        self.step = step
        self.spinbox.setSingleStep(step)

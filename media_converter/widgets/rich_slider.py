# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *


class RichSlider:
    """
    This class acts like a struct holding a slider and a spinbox together.
    The two widgets are connected so that any change to one are reflected on the other.
    """

    SLIDER_STEP = 5

    def __init__(
        self, title: str, unit: str = "px", lower_limit: int = 0, upper_limit: int = 100, step: int = SLIDER_STEP
    ) -> None:
        self.title = title
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.spinbox = QSpinBox()
        self.unitLabel = QLabel(unit)
        qconnect(self.slider.valueChanged, self.spinbox.setValue)
        qconnect(self.spinbox.valueChanged, self.slider.setValue)
        self.set_range(lower_limit, upper_limit)
        self._set_step(step)

    def set_range(self, start: int, stop: int) -> None:
        self.slider.setRange(start, stop)
        self.spinbox.setRange(start, stop)

    def set_upper_limit(self, limit: int) -> None:
        """
        Set the maximum value the user is allowed to apply.
        """
        return self.set_range(0, limit)

    def set_tooltip(self, tooltip: str) -> None:
        self.slider.setToolTip(tooltip)

    @property
    def widgets(self) -> tuple[QSlider, QSpinBox, QLabel]:
        return self.slider, self.spinbox, self.unitLabel

    @property
    def value(self) -> int:
        return self.slider.value()

    @value.setter
    def value(self, value: int) -> None:
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def _set_step(self, step: int) -> None:
        self.step = step
        self.spinbox.setSingleStep(step)

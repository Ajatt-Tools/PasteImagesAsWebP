# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import typing

from aqt.qt import *

SLIDER_STEP: int = 5


class RichSliderWidgets(typing.NamedTuple):
    """Expose RichSlider controls in layout order."""

    slider: QSlider
    spinbox: QSpinBox
    unit_label: QLabel


class RichSlider:
    """Keep a horizontal slider and a spin box synchronized."""

    def __init__(
        self, title: str, unit: str = "px", lower_limit: int = 0, upper_limit: int = 100, step: int = SLIDER_STEP
    ) -> None:
        """Create synchronized controls with a label and configured range."""
        self._title = title
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._spinbox = QSpinBox()
        self._unit_label = QLabel(unit)
        qconnect(self._slider.valueChanged, self._spinbox.setValue)
        qconnect(self._spinbox.valueChanged, self._slider.setValue)
        self.set_range(lower_limit, upper_limit)
        self._set_step(step)

    def set_range(self, start: int, stop: int) -> None:
        """Set the inclusive range for both controls."""
        self._slider.setRange(start, stop)
        self._spinbox.setRange(start, stop)

    def set_upper_limit(self, limit: int) -> None:
        """Set the maximum value while retaining the zero lower bound."""
        self.set_range(0, limit)

    def set_tooltip(self, tooltip: str) -> None:
        """Set the same tooltip on every visible control."""
        self._slider.setToolTip(tooltip)
        self._spinbox.setToolTip(tooltip)
        self._unit_label.setToolTip(tooltip)

    @property
    def title(self) -> str:
        """Return the label displayed beside the slider."""
        return self._title

    @property
    def widgets(self) -> RichSliderWidgets:
        """Return widgets in layout order."""
        return RichSliderWidgets(self._slider, self._spinbox, self._unit_label)

    @property
    def value(self) -> int:
        """Return the current shared value."""
        return self._slider.value()

    @value.setter
    def value(self, value: int) -> None:
        """Set the current value in both synchronized controls."""
        self._slider.setValue(value)
        self._spinbox.setValue(value)

    def _set_step(self, step: int) -> None:
        """Set keyboard and spin-box increment sizes."""
        self._slider.setSingleStep(step)
        self._spinbox.setSingleStep(step)

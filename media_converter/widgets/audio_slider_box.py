# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from aqt.qt import *

from ..widgets.rich_slider import RichSlider

MIN_AUDIO_BITRATE_K = 8
MAX_AUDIO_BITRATE_K = 600


class AudioSliderBox(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._slider = RichSlider("Bitrate", "kbit/s", lower_limit=MIN_AUDIO_BITRATE_K, upper_limit=MAX_AUDIO_BITRATE_K)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout()
        for widget in self._slider.widgets:
            layout.addWidget(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    @property
    def audio_bitrate_k(self) -> int:
        return self._slider.value

    @audio_bitrate_k.setter
    def audio_bitrate_k(self, kbit_per_s: int) -> None:
        self._slider.value = kbit_per_s

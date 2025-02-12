# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools

from aqt.qt import *

from ..ajt_common.utils import q_emit
from ..ajt_common.widget_placement import place_widgets_in_grid
from ..config import MediaConverterConfig
from ..dialogs.settings_dialog_base import ConfigPropMixIn, WidgetHasName


class ScaleSettings(QGroupBox, WidgetHasName, ConfigPropMixIn):
    """
    A widget where the user can scale the loaded image in one keypress (0.5x, 1x, 2x, etc.)
    """

    factor_changed = pyqtSignal(float)
    name: str = "Scale settings"

    def __init__(self, config: MediaConverterConfig, title: str, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self.setTitle(title)
        self._setup_ui()
        self._add_tooltips()

    def _setup_ui(self) -> None:
        self.setLayout(self.create_scale_options_grid())

    def create_scale_options_grid(self) -> QGridLayout:
        factors = (1 / 8, 1 / 4, 1 / 2, 1, 1.5, 2)
        widgets = []
        for factor in factors:
            button = QPushButton(f"{factor}x")
            qconnect(button.clicked, functools.partial(self.on_factor_changed, factor))
            widgets.append(button)
        return place_widgets_in_grid(widgets, n_columns=3, alignment=None)

    def on_factor_changed(self, factor: float) -> None:
        q_emit(self.factor_changed, factor)

    def _add_tooltips(self) -> None:
        pass

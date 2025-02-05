# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import qconnect
from aqt.qt import *

from ..config import MediaConverterConfig
from ..consts import ADDON_FULL_NAME, ADDON_NAME, WINDOW_MIN_WIDTH


ADDON_NAME_SNAKE = ADDON_NAME.lower().replace(' ', '_')

def make_accept_reject_box() -> QDialogButtonBox:
    return QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)


class ConfigPropMixIn:
    _config: MediaConverterConfig

    @property
    def config(self) -> MediaConverterConfig:
        assert self._config is not None
        return self._config


class HasNameMixIn(QWidget):
    name: str = "undefined"


class SettingsDialogBase(QDialog, ConfigPropMixIn, HasNameMixIn):
    name = f"ajt__{ADDON_NAME_SNAKE}_settings_dialog"

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle(ADDON_FULL_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self._main_vbox = QVBoxLayout()
        self._button_box = make_accept_reject_box()
        self.setLayout(self._main_vbox)

    @property
    def button_box(self) -> QDialogButtonBox:
        return self._button_box

    @property
    def main_vbox(self) -> QVBoxLayout:
        return self._main_vbox

    def setup_bottom_button_box(self) -> None:
        """
        Adds the button box at the bottom of the main layout and connects the Accept and Reject buttons.
        """
        qconnect(self._button_box.accepted, self.accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

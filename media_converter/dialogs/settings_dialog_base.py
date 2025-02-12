# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom

from ..ajt_common.about_menu import tweak_window
from ..ajt_common.addon_config import MgrPropMixIn
from ..config import MediaConverterConfig
from ..consts import ADDON_FULL_NAME, ADDON_NAME_SNAKE, WINDOW_MIN_WIDTH


def make_accept_reject_box() -> QDialogButtonBox:
    return QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)


class ConfigPropMixIn:
    _config: MediaConverterConfig

    @property
    def config(self) -> MediaConverterConfig:
        assert self._config is not None
        return self._config


class WidgetHasName(QWidget):
    name: str = "undefined"


class SettingsDialogBase(QDialog, ConfigPropMixIn, MgrPropMixIn):
    name: str = f"ajt__{ADDON_NAME_SNAKE}_settings_dialog"

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self.setWindowTitle(ADDON_FULL_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self._main_vbox = QVBoxLayout()
        self._button_box = make_accept_reject_box()
        self.setLayout(self._main_vbox)
        tweak_window(self)

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


class SettingsTabs(QTabWidget):
    """
    A widget that accepts a list of widgets and groups them into tabs.
    """

    _config: MediaConverterConfig

    def __init__(
        self,
        config: MediaConverterConfig,
        *tabs: WidgetHasName,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        for widget in tabs:
            self.addTab(widget, widget.name)


class AnkiSaveAndRestoreGeomDialog(QDialog):
    """
    A dialog running inside Anki should save and restore its position and size when closed/opened.
    """

    name: str

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        assert isinstance(self.name, str) and self.name, "Dialog name must be set."
        restoreGeom(self, self.name, adjustSize=True)
        print(f"restored geom for {self.name}")

    def _save_geom(self) -> None:
        saveGeom(self, self.name)
        print(f"saved geom for {self.name}")

    def accept(self) -> None:
        self._save_geom()
        return super().accept()

    def reject(self) -> None:
        self._save_geom()
        return super().reject()

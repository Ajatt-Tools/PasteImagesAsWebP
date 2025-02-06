# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import cast

from aqt.addons import AddonsDialog, ConfigEditor
from aqt.qt import *

from ..config import MediaConverterConfig
from ..consts import THIS_ADDON_MODULE
from ..widgets.audio_settings_widget import AudioSettings
from ..widgets.behavior_settings_widget import BehaviorSettings
from ..widgets.image_settings_widget import ImageSettings
from .settings_dialog_base import (
    ADDON_NAME_SNAKE,
    AnkiSaveAndRestoreGeomDialog,
    SettingsDialogBase,
    SettingsTabs,
)


class MainSettingsDialog(SettingsDialogBase):
    """Dialog available from the "AJT" menu (main window)."""

    name: str = f"ajt__{ADDON_NAME_SNAKE}_main_menu_dialog"
    _tabs: SettingsTabs
    _image_settings: ImageSettings
    _audio_settings: AudioSettings

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(config, parent)
        self._image_settings = ImageSettings(config=self.config)
        self._audio_settings = AudioSettings(config=self.config)
        self._behavior_settings = BehaviorSettings(config=self.config)
        self._tabs = SettingsTabs(self.config, self._image_settings, self._audio_settings, self._behavior_settings)
        self._setup_ui()
        self.setup_bottom_button_box()
        self.set_initial_values()

    def _setup_ui(self) -> None:
        self.main_vbox.addWidget(self._tabs)
        self.main_vbox.addStretch()
        self.main_vbox.addWidget(self.button_box)

    def set_initial_values(self) -> None:
        self._image_settings.set_initial_values()
        self._audio_settings.set_initial_values()
        self._behavior_settings.set_initial_values()

    def accept(self) -> None:
        self._image_settings.pass_settings_to_config()
        self._audio_settings.pass_settings_to_config()
        self._behavior_settings.pass_settings_to_config()
        self.config.write_config()
        return super().accept()


class AnkiMainSettingsDialog(MainSettingsDialog, AnkiSaveAndRestoreGeomDialog):
    """
    Adds methods that work only when Anki is running.
    """

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(config, parent)
        self._add_advanced_button()

    def _add_advanced_button(self) -> None:
        """
        Add the "Show advanced settings" button to the bottom button box (Okay, Cancel).
        """

        def advanced_clicked() -> None:
            d = ConfigEditor(cast(AddonsDialog, self), THIS_ADDON_MODULE, self.config.dict_copy())
            qconnect(d.accepted, self.set_initial_values)

        b = self.button_box.addButton("Advanced", QDialogButtonBox.ButtonRole.HelpRole)
        qconnect(b.clicked, advanced_clicked)

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from ..ajt_common.enum_select_combo import EnumSelectCombo
from ..config import AudioContainer, MediaConverterConfig
from .audio_slider_box import AudioSliderBox
from .settings_dialog_base import ConfigPropMixIn, HasNameMixIn


class AudioSettings(HasNameMixIn, ConfigPropMixIn):
    name: str = "Audio settings"
    _audio_container_combo: EnumSelectCombo

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._enable_checkbox = QCheckBox("Enable audio conversion")
        self._audio_container_combo = EnumSelectCombo(enum_type=AudioContainer)
        self._bitrate_slider = AudioSliderBox()
        self._layout = QFormLayout()
        self._setup_ui()
        self._add_tooltips()

    def _setup_ui(self) -> None:
        self._layout.addRow(self._enable_checkbox)
        self._layout.addRow("Audio container", self._audio_container_combo)
        self._layout.addRow("Audio bitrate", self._bitrate_slider)
        self.setLayout(self._layout)

    def _add_tooltips(self) -> None:
        self._enable_checkbox.setToolTip(
            "Enable conversion of audio files.\n"
            "FFmpeg must be installed in the system.\n"
            "If running Arch, run `sudo pacman -S ffmpeg` to install it."
        )
        self._audio_container_combo.setToolTip(
            "Audio container, or the file extension\n"
            "that will be used for audio files.\n"
            "Choose the one that works on your computer.\n"
            "Regardless of the chosen container, the target codec is always Opus."
        )

    def set_initial_values(self) -> None:
        self._enable_checkbox.setChecked(self.config.enable_audio_conversion)
        self._audio_container_combo.setCurrentName(self.config.audio_container)
        self._bitrate_slider.audio_bitrate_k = self.config.audio_bitrate_k

    def pass_settings_to_config(self) -> None:
        self.config["enable_audio_conversion"] = self._enable_checkbox.isChecked()
        self.config["audio_container"] = self._audio_container_combo.currentName()
        self.config.audio_bitrate_k = self._bitrate_slider.audio_bitrate_k

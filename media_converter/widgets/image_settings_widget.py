# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from aqt.qt import *

from ..config import MediaConverterConfig
from ..dialogs.settings_dialog_base import ConfigPropMixIn, WidgetHasName
from .image_slider_box import ImageSliderBox
from .presets_editor import PresetsEditor


class ImageSettings(WidgetHasName, ConfigPropMixIn):
    name: str = "Image settings"
    _enable_checkbox: QCheckBox
    _img_sliders: ImageSliderBox
    _presets_editor: PresetsEditor

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._layout = QFormLayout()
        self._enable_checkbox = QCheckBox("Enable image conversion")
        self._img_sliders = ImageSliderBox()
        self._presets_editor = PresetsEditor("Presets", sliders=self._img_sliders)
        self._setup_ui()
        self._add_tooltips()

    def _setup_ui(self) -> None:
        self._layout.addRow(self._enable_checkbox)
        self._layout.addRow(self._img_sliders)
        self._layout.addRow(self._presets_editor)
        self.setLayout(self._layout)

    def _add_tooltips(self) -> None:
        self._enable_checkbox.setToolTip(
            "Enable conversion of image files.\n"
            "When target image format is set to `Avif`,\n"
            "FFmpeg must be installed in the system.\n"
            "If running Arch, run `sudo pacman -S ffmpeg` to install it."
        )

    def set_initial_values(self) -> None:
        self._enable_checkbox.setChecked(self.config.enable_image_conversion)
        self._img_sliders.set_limits(self.config["max_image_width"], self.config["max_image_height"])
        self._img_sliders.image_width = self.config.image_width
        self._img_sliders.image_height = self.config.image_height
        self._img_sliders.image_quality = self.config.image_quality
        self._presets_editor.set_items(self.config["saved_presets"])

    def pass_settings_to_config(self) -> None:
        self.config["enable_image_conversion"] = self._enable_checkbox.isChecked()
        self.config.update(self._img_sliders.as_dict())
        self.config["saved_presets"] = self._presets_editor.as_list()

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import qconnect

from ..config import MediaConverterConfig
from ..consts import ADDON_NAME_SNAKE
from ..utils.show_options import ImageDimensions
from ..widgets.image_settings_widget import ImageSettings
from ..widgets.scale_settings_widget import ScaleSettings
from .settings_dialog_base import AnkiSaveAndRestoreGeomDialog, SettingsDialogBase


class PasteImageDialog(SettingsDialogBase):
    """Dialog shown on paste."""

    name: str = f"ajt__{ADDON_NAME_SNAKE}_paste_image_dialog"
    _image_settings: ImageSettings
    _scale_settings: ScaleSettings
    _dimensions: ImageDimensions

    def __init__(self, config: MediaConverterConfig, dimensions: ImageDimensions, parent=None) -> None:
        super().__init__(config, parent)
        self._dimensions = dimensions
        self._image_settings = ImageSettings(config=self.config)
        self._scale_settings = ScaleSettings(
            config=self.config, title=f"Original size: {self._dimensions.width} x {self._dimensions.height} px"
        )
        self._setup_ui()
        self.setup_bottom_button_box()
        self.set_initial_values()
        qconnect(self._scale_settings.factor_changed, self._set_factor)

    def _setup_ui(self) -> None:
        self.main_vbox.addWidget(self._image_settings)
        self.main_vbox.addWidget(self._scale_settings)
        self.main_vbox.addStretch()
        self.main_vbox.addWidget(self.button_box)

    def set_initial_values(self) -> None:
        self._image_settings.set_initial_values()

    def _set_factor(self, factor: float) -> None:
        self._image_settings.set_dimensions(
            width=int(self._dimensions.width * factor), height=int(self._dimensions.height * factor)
        )

    def accept(self) -> None:
        self._image_settings.pass_settings_to_config()
        self.config.write_config()
        return super().accept()


class AnkiPasteImageDialog(PasteImageDialog, AnkiSaveAndRestoreGeomDialog):
    """
    Adds methods that work only when Anki is running.
    """

    def __init__(self, config: MediaConverterConfig, dimensions: ImageDimensions, parent=None) -> None:
        super().__init__(config, dimensions, parent)

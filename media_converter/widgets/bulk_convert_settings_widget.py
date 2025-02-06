# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from ..ajt_common.multiple_choice_selector import MultipleChoiceSelector
from ..config import ImageFormat, MediaConverterConfig
from .settings_dialog_base import ConfigPropMixIn, HasNameMixIn


class EnableReconvertCheckbox(QCheckBox):
    def __init__(self, enabled_image_format: ImageFormat) -> None:
        super().__init__()
        self.setText(f"Reconvert existing {enabled_image_format.name} images")


class BulkConvertSettings(HasNameMixIn, ConfigPropMixIn):
    name: str = "Bulk-convert settings"
    _field_selector: MultipleChoiceSelector
    _reconvert_checkbox: QCheckBox

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._field_selector = MultipleChoiceSelector()
        self._reconvert_checkbox = EnableReconvertCheckbox(self.config.image_format)
        self._layout = QFormLayout()
        self._setup_ui()
        self._add_tooltips()

    @property
    def field_selector(self) -> MultipleChoiceSelector:
        return self._field_selector

    def _setup_ui(self) -> None:
        self._layout.addRow(self._field_selector)
        self._layout.addRow(self._reconvert_checkbox)
        self.setLayout(self._layout)

    def _add_tooltips(self) -> None:
        self._field_selector.setToolTip(
            "When enabled, search for image files only in selected fields.\n" "When disabled, search in all fields."
        )
        self._reconvert_checkbox.setToolTip(
            "If an image was converted to the target format before,\n"
            "convert it again.\n"
            "For example, change quality or dimensions."
        )

    def set_initial_values(self, all_field_names: list[str]) -> None:
        self._field_selector.set_texts(all_field_names)
        self._field_selector.set_checked_texts(self.config["bulk_convert_fields"])
        self._reconvert_checkbox.setChecked(self.config.bulk_reconvert)

    def pass_settings_to_config(self) -> None:
        self.config["bulk_convert_fields"] = self._field_selector.checked_texts()
        self.config.bulk_reconvert = self._reconvert_checkbox.isChecked()

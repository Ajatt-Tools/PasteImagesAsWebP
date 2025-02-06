# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from ..ajt_common.anki_field_selector import AnkiFieldSelector
from ..ajt_common.checkable_combobox import CheckableComboBox
from ..ajt_common.enum_select_combo import EnumSelectCombo
from ..config import ImageFormat, MediaConverterConfig
from ..dialogs.settings_dialog_base import ConfigPropMixIn, WidgetHasName
from ..utils.converter_interfaces import FileNamePatterns
from ..utils.show_options import ShowOptions

# Keys in the config file that will be converted to checkboxes.
VISIBLE_BOOL_CONFIG_KEYS = {
    "drag_and_drop": "Convert images on drag and drop",
    "copy_paste": "Convert images on copy-paste",
    "convert_on_note_add": "Convert when AnkiConnect creates new notes",
    "preserve_original_filenames": "Preserve original filenames, if available",
    "avoid_upscaling": "Avoid upscaling",
    "show_editor_button": "Show a Converter button on the Editor Toolbar",
    "show_context_menu_entry": "Show a separate context menu item",
}


def create_when_show_dialog_combo_box() -> CheckableComboBox:
    """
    When to show the settings dialog: (toolbar button clicked, when a file is drag-and-dropped, etc.)
    """
    combobox = CheckableComboBox()
    for option in ShowOptions:
        combobox.addCheckableItem(option.value, option)
    return combobox


def create_filename_pattern_combo_box() -> QComboBox:
    """
    How to name the newly created files.
    """
    combobox = QComboBox()
    for option in FileNamePatterns().all_examples():
        combobox.addItem(option)
    return combobox


class BehaviorSettings(WidgetHasName, ConfigPropMixIn):
    name: str = "Behavior settings"

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._layout = QFormLayout()
        # Create widgets
        self._image_format_combo_box = EnumSelectCombo(ImageFormat)
        self._when_show_dialog_combo_box = create_when_show_dialog_combo_box()
        self._filename_pattern_combo_box = create_filename_pattern_combo_box()
        self._custom_name_field_combo_box = AnkiFieldSelector(self)
        self._excluded_image_containers_edit = QLineEdit()
        self._excluded_audio_containers_edit = QLineEdit()
        self._checkboxes = {key: QCheckBox(text) for key, text in VISIBLE_BOOL_CONFIG_KEYS.items()}
        # Setup UI
        self._setup_ui()
        self._add_tooltips()

    def _setup_ui(self) -> None:
        self._layout.addRow("Image format", self._image_format_combo_box)
        self._layout.addRow("Show Settings", self._when_show_dialog_combo_box)
        self._layout.addRow("Filename pattern", self._filename_pattern_combo_box)
        self._layout.addRow("Custom name field", self._custom_name_field_combo_box)
        self._layout.addRow("Excluded image formats", self._excluded_image_containers_edit)
        self._layout.addRow("Excluded audio formats", self._excluded_audio_containers_edit)
        for widget in self._checkboxes.values():
            self._layout.addRow(widget)
        self.setLayout(self._layout)

    def _add_tooltips(self) -> None:
        # TODO handle audio files when a note is added
        self._checkboxes["convert_on_note_add"].setToolTip(
            "Convert images when a new note is added by an external tool, such as AnkiConnect.\n"
            "Does not apply to the native Add dialog."
        )
        self._excluded_image_containers_edit.setToolTip(
            "A comma-separated list of image file formats (extensions without the dot)\n"
            "that should be skipped when converting image files."
        )
        self._excluded_audio_containers_edit.setToolTip(
            "A comma-separated list of audio file formats (extensions without the dot)\n"
            "that should be skipped when converting audio files."
        )

    def set_initial_values(self) -> None:
        self._image_format_combo_box.setCurrentName(self.config.image_format)
        self._when_show_dialog_combo_box.setCheckedData(self.config.show_settings())
        self._filename_pattern_combo_box.setCurrentIndex(self.config["filename_pattern_num"])
        self._custom_name_field_combo_box.setCurrentText(self.config["custom_name_field"])
        self._excluded_image_containers_edit.setText(self.config["excluded_image_containers"].lower())
        self._excluded_audio_containers_edit.setText(self.config["excluded_audio_containers"].lower())
        for key, widget in self._checkboxes.items():
            widget.setChecked(self.config[key])

    def pass_settings_to_config(self) -> None:
        self.config.set_show_options(self._when_show_dialog_combo_box.checkedData())
        self.config["image_format"] = self._image_format_combo_box.currentName()
        self.config["filename_pattern_num"] = self._filename_pattern_combo_box.currentIndex()
        self.config["custom_name_field"] = self._custom_name_field_combo_box.currentText()
        self.config["excluded_image_containers"] = self._excluded_image_containers_edit.text().lower().strip()
        self.config["excluded_audio_containers"] = self._excluded_audio_containers_edit.text().lower().strip()
        for key, widget in self._checkboxes.items():
            self.config[key] = widget.isChecked()

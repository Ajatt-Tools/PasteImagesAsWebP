# Paste Images As WebP add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.

import itertools
from typing import cast

from anki.notes import Note
from aqt import mw
from aqt.addons import ConfigEditor, AddonsDialog
from aqt.browser import Browser
from aqt.utils import showInfo

from .ajt_common.addon_config import MgrPropMixIn
from .ajt_common.anki_field_selector import AnkiFieldSelector
from .ajt_common.checkable_combobox import CheckableComboBox
from .ajt_common.multiple_choice_selector import MultipleChoiceSelector
from .common import *
from .config import config
from .consts import *
from .utils.converter_interfaces import FileNamePatterns
from .utils.show_options import ShowOptions
from .widgets.image_slider_box import ImageSliderBox
from .widgets.presets_editor import PresetsEditor


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cast(QDialog, self).setWindowTitle(ADDON_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self._sliders = ImageSliderBox("Image parameters")
        self._presets_editor = PresetsEditor("Presets", sliders=self._sliders)
        self._main_vbox = QVBoxLayout()
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)

    def setup_ui(self):
        self.setLayout(self.create_main_layout())
        self.populate_main_vbox()
        self.setup_logic()
        self.set_initial_values()

    def exec(self):
        self.setup_ui()
        return super().exec()

    def create_main_layout(self):
        layout = QVBoxLayout()
        layout.addLayout(self._main_vbox)
        layout.addStretch()
        layout.addWidget(self._button_box)
        return layout

    def populate_main_vbox(self):
        self._main_vbox.addWidget(self._sliders)
        self._main_vbox.addWidget(self._presets_editor)

    def setup_logic(self):
        qconnect(self._button_box.accepted, self.accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def set_initial_values(self):
        self._sliders.set_limits(config["max_image_width"], config["max_image_height"])
        self._sliders.populate(config)
        self._presets_editor.set_items(config["saved_presets"])

    def accept(self):
        config.update(self._sliders.as_dict())
        config["saved_presets"] = self._presets_editor.as_list()
        config.write_config()
        return super().accept()


def get_all_keys(notes: Iterable[Note]) -> list[str]:
    return sorted(set(itertools.chain(*(note.keys() for note in notes))))


class BulkConvertDialog(SettingsDialog):
    """Dialog shown on bulk-convert."""

    def __init__(self, *args, **kwargs):
        self._field_selector = MultipleChoiceSelector()
        self._reconvert_checkbox = QCheckBox("Reconvert existing WebP images")
        super().__init__(*args, **kwargs)

    def selected_fields(self) -> list[str]:
        return self._field_selector.checked_texts()

    def selected_notes(self) -> Iterable[Note]:
        return (mw.col.get_note(nid) for nid in cast(Browser, self.parent()).selectedNotes())

    def populate_main_vbox(self):
        super().populate_main_vbox()
        self._main_vbox.addWidget(self._field_selector)
        self._main_vbox.addWidget(self._reconvert_checkbox)

    def set_initial_values(self):
        self._field_selector.set_texts(get_all_keys(self.selected_notes()))
        self._field_selector.set_checked_texts(config["bulk_convert_fields"])
        self._reconvert_checkbox.setChecked(config["bulk_reconvert_webp"])
        super().set_initial_values()

    def accept(self):
        if self._field_selector.isChecked() and not self._field_selector.checked_texts():
            showInfo(title="Can't accept settings", text="No fields selected. Nothing to convert.")
        else:
            config["bulk_convert_fields"] = self._field_selector.checked_texts()
            config["bulk_reconvert_webp"] = self._reconvert_checkbox.isChecked()
            return super().accept()


class PasteDialog(SettingsDialog):
    """Dialog shown on paste."""

    def __init__(self, *args, image: ImageDimensions, **kwargs):
        self.image = image
        super().__init__(*args, **kwargs)

    def populate_main_vbox(self):
        super().populate_main_vbox()
        self._main_vbox.addWidget(self.create_scale_settings_group_box())

    def create_scale_settings_group_box(self):
        gbox = QGroupBox(f"Original size: {self.image.width} x {self.image.height} px")
        gbox.setLayout(self.create_scale_options_grid())
        return gbox

    def adjust_sliders(self, factor: float):
        if self._sliders.width > 0:
            self._sliders.width = int(self.image.width * factor)
        if self._sliders.height > 0:
            self._sliders.height = int(self.image.height * factor)

    def create_scale_options_grid(self):
        grid = QGridLayout()
        factors = (1 / 8, 1 / 4, 1 / 2, 1, 1.5, 2)
        columns = 3
        for index, factor in enumerate(factors):
            i = int(index / columns)
            j = index - (i * columns)
            button = QPushButton(f"{factor}x")
            qconnect(button.clicked, lambda _, f=factor: self.adjust_sliders(f))
            grid.addWidget(button, i, j)
        return grid


class SettingsMenuDialog(SettingsDialog, MgrPropMixIn):
    """Settings dialog available from the main menu."""

    _checkboxes = {
        'drag_and_drop': 'Convert images on drag and drop',
        'copy_paste': 'Convert images on copy-paste',
        'convert_on_note_add': 'Convert when AnkiConnect creates new notes',
        'preserve_original_filenames': 'Preserve original filenames, if available',
        'avoid_upscaling': 'Avoid upscaling',
        'show_editor_button': 'Show a WebP button on the Editor Toolbar',
        'show_context_menu_entry': 'Show a separate context menu item',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.when_show_dialog_combo_box = self.create_when_show_dialog_combo_box()
        self.filename_pattern_combo_box = self.create_filename_pattern_combo_box()
        self.custom_name_field_combo_box = AnkiFieldSelector(self)
        self.checkboxes = {key: QCheckBox(text) for key, text in self._checkboxes.items()}
        self.add_advanced_button()
        self.add_tooltips()

    def add_tooltips(self):
        self.checkboxes['convert_on_note_add'].setToolTip(
            "Convert images when a new note is added by an external tool, such as AnkiConnect.\n"
            "Does not apply to the native Add dialog."
        )

    def add_advanced_button(self):
        def advanced_clicked():
            d = ConfigEditor(cast(AddonsDialog, self), THIS_ADDON_MODULE, config.dict_copy())
            qconnect(d.accepted, self.set_initial_values)

        b = self._button_box.addButton("Advanced", QDialogButtonBox.ButtonRole.HelpRole)
        qconnect(b.clicked, advanced_clicked)

    @staticmethod
    def create_when_show_dialog_combo_box() -> CheckableComboBox:
        combobox = CheckableComboBox()
        for option in ShowOptions:
            combobox.addCheckableItem(option.value, option)
        return combobox

    @staticmethod
    def create_filename_pattern_combo_box() -> QComboBox:
        combobox = QComboBox()
        for option in FileNamePatterns().all_examples():
            combobox.addItem(option)
        return combobox

    def populate_main_vbox(self):
        super().populate_main_vbox()
        self._main_vbox.addWidget(self.create_additional_settings_group_box())

    def create_additional_settings_group_box(self) -> QGroupBox:
        """Creates the "Behavior" groupbox showing additional settings and checkboxes."""

        def create_combo_boxes_layout():
            layout = QFormLayout()
            layout.addRow("Show this dialog", self.when_show_dialog_combo_box)
            layout.addRow("Filename pattern", self.filename_pattern_combo_box)
            layout.addRow("Custom name field", self.custom_name_field_combo_box)
            return layout

        def create_inner_layout():
            vbox = QVBoxLayout()
            vbox.addLayout(create_combo_boxes_layout())
            for widget in self.checkboxes.values():
                vbox.addWidget(widget)
            return vbox

        gbox = QGroupBox("Behavior")
        gbox.setLayout(create_inner_layout())
        return gbox

    def set_initial_values(self):
        super().set_initial_values()
        self.when_show_dialog_combo_box.setCheckedData(config.show_settings())
        self.filename_pattern_combo_box.setCurrentIndex(config["filename_pattern_num"])
        self.custom_name_field_combo_box.setCurrentText(config["custom_name_field"])

        for key, widget in self.checkboxes.items():
            widget.setChecked(config[key])

    def accept(self):
        config.set_show_options(self.when_show_dialog_combo_box.checkedData())
        config["filename_pattern_num"] = self.filename_pattern_combo_box.currentIndex()
        config["custom_name_field"] = self.custom_name_field_combo_box.currentText()
        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()

        return super().accept()

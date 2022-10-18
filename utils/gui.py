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
from enum import Enum
from typing import NamedTuple, Iterable, Tuple, Optional, List, Dict

from anki.notes import Note
from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from .checkable_combobox import CheckableComboBox
from .file_paths_factory import FilePathFactory
from ..config import config, write_config
from ..consts import *


class ShowOptions(Enum):
    always = "Always"
    menus = "Toolbar and menus"
    drag_and_drop = "On drag and drop"
    never = "Never"

    def __eq__(self, other: str):
        return self.name == other

    @classmethod
    def index_of(cls, name):
        for index, item in enumerate(cls):
            if name == item.name:
                return index
        return 0


class RichSlider:
    """
    This class acts like a struct holding a slider and a spinbox together.
    The two widgets are connected so that any change to one are reflected on the other.
    """

    SLIDER_STEP = 5

    def __init__(self, title: str, unit: str = "px", limit: int = 100, step: int = SLIDER_STEP):
        self.title = title
        self.slider = QSlider(Qt.Horizontal)
        self.spinbox = QSpinBox()
        self.unitLabel = QLabel(unit)
        qconnect(self.slider.valueChanged, self.spinbox.setValue)
        qconnect(self.spinbox.valueChanged, self.slider.setValue)
        self._set_step(step)
        self._set_range(0, limit)

    def set_tooltip(self, tooltip: str):
        self.slider.setToolTip(tooltip)

    @property
    def widgets(self) -> Tuple[QWidget, ...]:
        return self.slider, self.spinbox, self.unitLabel

    @property
    def value(self) -> int:
        return self.slider.value()

    @value.setter
    def value(self, value: int):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def _set_range(self, start: int, stop: int):
        self.slider.setRange(start, stop)
        self.spinbox.setRange(start, stop)

    def _set_step(self, step: int):
        self.step = step
        self.spinbox.setSingleStep(step)


class ImageSliderBox(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sliders = {
            'image_width': RichSlider("Width", "px", limit=config['max_image_width']),
            'image_height': RichSlider("Height", "px", limit=config['max_image_height']),
            'image_quality': RichSlider("Quality", "%", limit=100),
        }
        self.setLayout(self.create_layout())
        self.set_tooltips()

    def as_dict(self) -> Dict[str, int]:
        return {key: slider.value for key, slider in self._sliders.items()}

    @property
    def quality(self) -> int:
        return self._sliders['image_quality'].value

    @property
    def width(self) -> int:
        return self._sliders['image_width'].value

    @width.setter
    def width(self, value: int):
        self._sliders['image_width'].value = value

    @property
    def height(self) -> int:
        return self._sliders['image_height'].value

    @height.setter
    def height(self, value: int):
        self._sliders['image_height'].value = value

    def create_layout(self) -> QLayout:
        grid = QGridLayout()
        for y_index, slider in enumerate(self._sliders.values()):
            grid.addWidget(QLabel(slider.title), y_index, 0)
            for x_index, widget in enumerate(slider.widgets):
                grid.addWidget(widget, y_index, x_index + 1)
        return grid

    def populate(self, custom_dict: Optional[Dict[str, int]] = None):
        for key, slider in self._sliders.items():
            slider.value = (custom_dict or config).get(key)

    def save_config(self):
        for key, slider in self._sliders.items():
            config[key] = slider.value

    def set_tooltips(self):
        side_tooltip = str(
            "Desired %s.\n"
            "If either of the width or height parameters is 0,\n"
            "the value will be calculated preserving the aspect-ratio.\n"
            "If both values are 0, no resizing is performed (not recommended)."
        )
        quality_tooltip = str(
            "Specify the compression factor between 0 and 100.\n"
            "A small factor produces a smaller file with lower quality.\n"
            "Best quality is achieved by using a value of 100."
        )
        self._sliders['image_width'].set_tooltip(side_tooltip % 'width')
        self._sliders['image_height'].set_tooltip(side_tooltip % 'height')
        self._sliders['image_quality'].set_tooltip(quality_tooltip)


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle(ADDON_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self._sliders = ImageSliderBox("Image parameters")
        self._main_vbox = QVBoxLayout()
        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

    def exec(self):
        self.setLayout(self.create_main_layout())
        self.populate_main_vbox()
        self.setup_logic()
        self.set_initial_values()
        return super().exec()

    def create_main_layout(self):
        layout = QVBoxLayout()
        layout.addLayout(self._main_vbox)
        layout.addStretch()
        layout.addWidget(self._button_box)
        return layout

    def populate_main_vbox(self):
        self._main_vbox.addWidget(self._sliders)

    def setup_logic(self):
        qconnect(self._button_box.accepted, self.on_accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.Ok).setFocus()

    def set_initial_values(self):
        self._sliders.populate()

    def on_accept(self):
        self._sliders.save_config()
        write_config()
        self.accept()


def get_all_keys(notes: Iterable[Note]) -> List[str]:
    return sorted(set(itertools.chain(*(note.keys() for note in notes))))


class FieldSelector(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._combo = CheckableComboBox()
        self.setTitle("Limit to field")
        self.setCheckable(True)
        self.setChecked(False)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._combo)

    def add_fields(self, fields: Iterable[str]):
        return self._combo.addCheckableTexts(fields)

    def selected_fields(self) -> List[str]:
        return list(self._combo.checkedTexts()) if self.isChecked() else []

    def set_fields(self, fields: Optional[List[str]]):
        if fields:
            self.setChecked(True)
            self._combo.setCheckedTexts(fields)
        else:
            self.setChecked(False)


class BulkConvertDialog(SettingsDialog):
    """Dialog shown on bulk-convert."""

    def __init__(self, *args, **kwargs):
        self._field_selector = FieldSelector()
        self._reconvert_checkbox = QCheckBox("Reconvert existing WebP images")
        super().__init__(*args, **kwargs)

    def selected_fields(self) -> List[str]:
        return self._field_selector.selected_fields()

    def selected_notes(self) -> Iterable[Note]:
        return (mw.col.get_note(nid) for nid in self.parent().selectedNotes())

    def populate_main_vbox(self):
        super().populate_main_vbox()
        self._main_vbox.addWidget(self._field_selector)
        self._main_vbox.addWidget(self._reconvert_checkbox)

    def set_initial_values(self):
        self._field_selector.add_fields(get_all_keys(self.selected_notes()))
        self._field_selector.set_fields(config.get('bulk_convert_fields'))
        self._reconvert_checkbox.setChecked(config.get('bulk_reconvert_webp'))
        super().set_initial_values()

    def on_accept(self):
        if self._field_selector.isChecked() and not self._field_selector.selected_fields():
            showInfo(title="Can't accept settings", text="No fields selected. Nothing to convert.")
        else:
            config['bulk_convert_fields'] = self._field_selector.selected_fields()
            config['bulk_reconvert_webp'] = self._reconvert_checkbox.isChecked()
            super().on_accept()


class ImageDimensions(NamedTuple):
    width: int
    height: int


class PasteDialog(SettingsDialog):
    """Dialog shown on paste."""

    def __init__(self, parent: QWidget, image: ImageDimensions, *args, **kwargs):
        self.image = image
        super().__init__(parent, *args, **kwargs)

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


def preset_to_str(preset: Dict[str, int]) -> str:
    return f"{preset['image_width']}x{preset['image_height']} @ {preset['image_quality']}"


class PresetsEditor(QGroupBox):
    def __init__(self, *args, sliders: ImageSliderBox, **kwargs):
        super().__init__(*args, **kwargs)
        self._sliders = sliders
        self.combo = QComboBox()
        self.add_current = QPushButton("Add current")
        self.remove_selected = QPushButton("Remove selected")
        self.apply_selected = QPushButton("Apply selected")
        self.setLayout(self.create_layout())
        self.connect_buttons()

    def create_layout(self) -> QLayout:
        layout = QGridLayout()
        layout.addWidget(self.combo, 0, 0, 1, 3)  # row, col, row-span, col-span
        layout.addWidget(self.add_current, 1, 0)
        layout.addWidget(self.remove_selected, 1, 1)
        layout.addWidget(self.apply_selected, 1, 2)
        return layout

    def as_list(self) -> List[Dict[str, int]]:
        return [
            self.combo.itemData(index)
            for index in range(self.combo.count())
        ]

    def add_items(self, items: List[Dict[str, int]]):
        for item in items:
            self.combo.addItem(preset_to_str(item), item)

    def add_new_preset(self):
        self.combo.addItem(preset_to_str(preset := self._sliders.as_dict()), preset)

    def apply_selected_preset(self):
        if data := self.combo.currentData():
            self._sliders.populate(data)

    def connect_buttons(self):
        qconnect(self.add_current.clicked, self.add_new_preset)
        qconnect(self.remove_selected.clicked, lambda: self.combo.removeItem(self.combo.currentIndex()))
        qconnect(self.apply_selected.clicked, self.apply_selected_preset)


class SettingsMenuDialog(SettingsDialog):
    """Settings dialog available from the main menu."""

    __checkboxes = {
        'drag_and_drop': 'Convert images on drag and drop',
        'copy_paste': 'Convert images on copy-paste',
        'avoid_upscaling': 'Avoid upscaling',
        'preserve_original_filenames': 'Preserve original filenames, if available',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.presets_editor = PresetsEditor("Presets", sliders=self._sliders)
        self.when_show_dialog_combo_box = self.create_when_show_dialog_combo_box()
        self.filename_pattern_combo_box = self.create_filename_pattern_combo_box()
        self.checkboxes = {key: QCheckBox(text) for key, text in self.__checkboxes.items()}

    @staticmethod
    def create_when_show_dialog_combo_box() -> QComboBox:
        combobox = QComboBox()
        for option in ShowOptions:
            combobox.addItem(option.value, option.name)
        return combobox

    @staticmethod
    def create_filename_pattern_combo_box() -> QComboBox:
        combobox = QComboBox()
        for option in FilePathFactory().patterns_populated:
            combobox.addItem(option)
        return combobox

    def populate_main_vbox(self):
        super().populate_main_vbox()
        self._main_vbox.addWidget(self.presets_editor)
        self._main_vbox.addWidget(self.create_additional_settings_group_box())

    def create_additional_settings_group_box(self) -> QGroupBox:
        def create_inner_vbox():
            vbox = QVBoxLayout()
            vbox.addLayout(self.create_combo_boxes_layout())
            for widget in self.checkboxes.values():
                vbox.addWidget(widget)
            return vbox

        gbox = QGroupBox("Behavior")
        gbox.setLayout(create_inner_vbox())
        return gbox

    def set_initial_values(self):
        super().set_initial_values()
        self.when_show_dialog_combo_box.setCurrentIndex(ShowOptions.index_of(config.get("show_settings")))
        self.filename_pattern_combo_box.setCurrentIndex(config.get("filename_pattern_num", 0))
        self.presets_editor.add_items(config.get('saved_presets', []))

        for key, widget in self.checkboxes.items():
            widget.setChecked(config[key])

    def create_combo_boxes_layout(self):
        layout = QFormLayout()
        layout.addRow("Show this dialog", self.when_show_dialog_combo_box)
        layout.addRow("Filename pattern", self.filename_pattern_combo_box)
        return layout

    def on_accept(self):
        config['show_settings'] = self.when_show_dialog_combo_box.currentData()
        config['filename_pattern_num'] = self.filename_pattern_combo_box.currentIndex()
        config['saved_presets'] = self.presets_editor.as_list()

        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()
        super().on_accept()

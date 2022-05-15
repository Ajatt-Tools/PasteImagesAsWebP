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
from typing import NamedTuple, Iterable, Tuple, Optional, List

from anki.notes import Note
from aqt import mw
from aqt.qt import *

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
        self.slider.valueChanged.connect(lambda val: self.spinbox.setValue(val))
        self.spinbox.valueChanged.connect(lambda val: self.slider.setValue(val))
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


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sliders = {
            'image_width': RichSlider("Width", "px", limit=config['max_image_width']),
            'image_height': RichSlider("Height", "px", limit=config['max_image_height']),
            'image_quality': RichSlider("Quality", "%", limit=100),
        }
        self._main_vbox = QVBoxLayout()
        self._button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(ADDON_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self.setLayout(self.create_main_layout())
        self.populate_main_vbox()
        self.setup_tool_tips()
        self.setup_logic()
        self.set_initial_values()

    def create_main_layout(self):
        layout = QVBoxLayout()
        layout.addLayout(self._main_vbox)
        layout.addStretch()
        layout.addWidget(self._button_box)
        return layout

    def populate_main_vbox(self):
        self._main_vbox.addWidget(self.create_sliders_group_box(self._sliders.values()))

    @staticmethod
    def create_sliders_group_box(sliders: Iterable[RichSlider]) -> QGroupBox:
        gbox = QGroupBox("Settings")
        grid = QGridLayout()
        for y_index, slider in enumerate(sliders):
            grid.addWidget(QLabel(slider.title), y_index, 0)
            for x_index, widget in enumerate(slider.widgets):
                grid.addWidget(widget, y_index, x_index + 1)

        gbox.setLayout(grid)
        return gbox

    def setup_tool_tips(self):
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

    def setup_logic(self):
        qconnect(self._button_box.accepted, self.on_accept)
        qconnect(self._button_box.rejected, self.reject)
        self._button_box.button(QDialogButtonBox.Ok).setFocus()

    def set_initial_values(self):
        for key, slider in self._sliders.items():
            slider.value = config.get(key)

    def on_accept(self):
        for key, slider in self._sliders.items():
            config[key] = slider.value
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

    def adjust_sliders(self, factor):
        for param in ('width', 'height'):
            if (widget := self._sliders[f'image_{param}']).value > 0:
                widget.value = int(getattr(self.image, param) * factor)

    def create_scale_options_grid(self):
        grid = QGridLayout()
        factors = (1 / 8, 1 / 4, 1 / 2, 1, 1.5, 2)
        columns = 3
        for index, factor in enumerate(factors):
            i = int(index / columns)
            j = index - (i * columns)
            button = QPushButton(f"{factor}x")
            button.clicked.connect(lambda _, f=factor: self.adjust_sliders(f))
            grid.addWidget(button, i, j)
        return grid


class SettingsMenuDialog(SettingsDialog):
    """Settings dialog available from the main menu."""

    __checkboxes = {
        'drag_and_drop': 'Convert images on drag and drop',
        'copy_paste': 'Convert images on copy-paste',
        'avoid_upscaling': 'Avoid upscaling',
        'preserve_original_filenames': 'Preserve original filenames, if available',
    }

    def __init__(self, *args, **kwargs):
        self.when_show_dialog_combo_box = self.create_when_show_dialog_combo_box()
        self.filename_pattern_combo_box = self.create_filename_pattern_combo_box()
        self.checkboxes = {key: QCheckBox(text) for key, text in self.__checkboxes.items()}
        super().__init__(*args, **kwargs)

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
        self._main_vbox.addWidget(self.create_additional_settings_group_box())

    def create_additional_settings_group_box(self):
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

        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()
        super().on_accept()

# -*- coding: utf-8 -*-

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

from enum import Enum
from typing import NamedTuple

from aqt.qt import *

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

    def __init__(self, title: str, unit: str = "px"):
        self.title = title
        self.step = 1
        self.slider = QSlider(Qt.Horizontal)
        self.spinbox = QSpinBox()
        self.unitLabel = QLabel(unit)
        self.slider.valueChanged.connect(lambda val: self.spinbox.setValue(val))
        self.spinbox.valueChanged.connect(lambda val: self.slider.setValue(val))

    def set_value(self, value: int):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def value(self) -> int:
        return self.slider.value()

    def set_range(self, start: int, stop: int):
        self.slider.setRange(start, stop)
        self.spinbox.setRange(start, stop)

    def set_step(self, step: int):
        self.step = step
        self.spinbox.setSingleStep(step)

    def set_tooltip(self, tooltip: str):
        self.slider.setToolTip(tooltip)

    def as_tuple(self):
        return self.slider, self.spinbox, self.unitLabel


class SettingsDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)
        self.sliderRow = QVBoxLayout()
        self.widthSlider = RichSlider("Width", "px")
        self.heightSlider = RichSlider("Height", "px")
        self.qualitySlider = RichSlider("Quality", "%")
        self.buttonRow = QHBoxLayout()
        self.okButton = QPushButton("Ok")
        self.cancelButton = QPushButton("Cancel")
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(ADDON_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)

        self.setLayout(self.create_main_layout())
        self.populate_slider_row()
        self.populate_button_row()
        self.setup_tool_tips()
        self.setup_logic()
        self.set_initial_values()

    def create_main_layout(self):
        layout = QVBoxLayout()
        layout.addLayout(self.sliderRow)
        layout.addStretch()
        layout.addLayout(self.buttonRow)
        return layout

    def populate_slider_row(self):
        self.sliderRow.addWidget(
            self.create_sliders_group_box(self.widthSlider, self.heightSlider, self.qualitySlider)
        )

    @staticmethod
    def create_sliders_group_box(*sliders) -> QGroupBox:
        gbox = QGroupBox("Settings")
        grid = QGridLayout()
        for y_index, slider in enumerate(sliders):
            grid.addWidget(QLabel(slider.title), y_index, 0)
            for x_index, widget in enumerate(slider.as_tuple()):
                grid.addWidget(widget, y_index, x_index + 1)

        gbox.setLayout(grid)
        return gbox

    def populate_button_row(self):
        for button in (self.okButton, self.cancelButton):
            button.setMinimumHeight(BUTTON_MIN_HEIGHT)
            self.buttonRow.addWidget(button)
        self.buttonRow.addStretch()

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
        self.widthSlider.set_tooltip(side_tooltip % 'width')
        self.heightSlider.set_tooltip(side_tooltip % 'height')
        self.qualitySlider.set_tooltip(quality_tooltip)

    def setup_logic(self):
        for slider, limit in zip((self.widthSlider, self.heightSlider, self.qualitySlider), self.limits()):
            slider.set_range(0, limit)
            slider.set_step(SLIDER_STEP)

        self.okButton.clicked.connect(self.dialog_accept)
        self.cancelButton.clicked.connect(self.dialog_reject)

    @staticmethod
    def limits() -> tuple:
        return config.get("max_image_width", 800), config.get("max_image_height", 600), 100

    def set_initial_values(self):
        self.widthSlider.set_value(config.get("image_width"))
        self.heightSlider.set_value(config.get("image_height"))
        self.qualitySlider.set_value(config.get("image_quality"))

    def dialog_accept(self):
        config["image_width"] = self.widthSlider.value()
        config["image_height"] = self.heightSlider.value()
        config["image_quality"] = self.qualitySlider.value()
        write_config()
        self.accept()

    def dialog_reject(self):
        self.reject()


class ImageDimensions(NamedTuple):
    width: int
    height: int


class PasteDialog(SettingsDialog):
    def __init__(self, parent, image: ImageDimensions, *args, **kwargs):
        self.image = image
        super(PasteDialog, self).__init__(parent, *args, **kwargs)

    def populate_slider_row(self):
        super(PasteDialog, self).populate_slider_row()
        self.sliderRow.addWidget(self.create_scale_settings_group_box())

    def create_scale_settings_group_box(self):
        gbox = QGroupBox(f"Original size: {self.image.width} x {self.image.height} px")
        gbox.setLayout(self.create_scale_options_grid())
        return gbox

    def adjust_sliders(self, factor):
        if self.widthSlider.value() > 0:
            self.widthSlider.set_value(int(self.image.width * factor))
        if self.heightSlider.value() > 0:
            self.heightSlider.set_value(int(self.image.height * factor))

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
    __checkboxes = {
        'drag_and_drop': 'Convert images on drag and drop',
        'copy_paste': 'Convert images on copy-paste',
        'avoid_upscaling': 'Avoid upscaling',
    }

    def __init__(self, *args, **kwargs):
        self.whenShowDialogComboBox = self.create_when_show_dialog_combo_box()
        self.checkboxes = {key: QCheckBox(text) for key, text in self.__checkboxes.items()}
        super(SettingsMenuDialog, self).__init__(*args, **kwargs)

    @staticmethod
    def create_when_show_dialog_combo_box():
        combobox = QComboBox()
        for option in ShowOptions:
            combobox.addItem(option.value, option.name)
        return combobox

    def populate_slider_row(self):
        super(SettingsMenuDialog, self).populate_slider_row()
        self.sliderRow.addWidget(self.create_additional_settings_group_box())

    def create_additional_settings_group_box(self):
        def create_inner_vbox():
            vbox = QVBoxLayout()
            vbox.addLayout(self.create_show_settings_layout())
            for widget in self.checkboxes.values():
                vbox.addWidget(widget)
            return vbox

        gbox = QGroupBox("Behavior")
        gbox.setLayout(create_inner_vbox())
        return gbox

    def set_initial_values(self):
        super(SettingsMenuDialog, self).set_initial_values()
        self.whenShowDialogComboBox.setCurrentIndex(ShowOptions.index_of(config.get("show_settings")))
        for key, widget in self.checkboxes.items():
            widget.setChecked(config[key])

    def create_show_settings_layout(self):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Show this dialog"))
        hbox.addWidget(self.whenShowDialogComboBox, 1)
        return hbox

    def dialog_accept(self):
        config["show_settings"] = self.whenShowDialogComboBox.currentData()
        for key, widget in self.checkboxes.items():
            config[key] = widget.isChecked()
        super(SettingsMenuDialog, self).dialog_accept()

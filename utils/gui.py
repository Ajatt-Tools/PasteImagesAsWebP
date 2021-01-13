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

from aqt import mw
from aqt.qt import *

from ..config import config
from ..consts import *


class ShowOptions(Enum):
    always = "Always"
    toolbar = "Toolbar and menus"
    drag_and_drop = "On drag and drop"
    never = "Never"

    def __eq__(self, other: str):
        return self.name == other

    @classmethod
    def indexOf(cls, name):
        for index, item in enumerate(cls):
            if name == item.name:
                return index
        return 0


class RichSlider:
    def __init__(self, title: str, unit: str = "px"):
        self.title = title
        self.step = 1
        self.slider = QSlider(Qt.Horizontal)
        self.spinbox = QSpinBox()
        self.unitLabel = QLabel(unit)
        self.slider.valueChanged.connect(self._setSpinBoxValue)
        self.spinbox.valueChanged.connect(self._setDiscreteValue)

    def setValue(self, value: int):
        self.slider.setValue(value)
        self.spinbox.setValue(value)

    def _setSpinBoxValue(self, value: int):
        """Set the slider value to the spinbox"""
        # Prevent the spinbox from backfiring, then update.
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)

    def _setDiscreteValue(self, value: int):
        """Spinbox changes its value in steps"""
        discrete_value = int(value / self.step) * self.step
        self.slider.setValue(discrete_value)
        self.spinbox.setValue(discrete_value)

    def value(self) -> int:
        return self.slider.value()

    def setRange(self, start: int, stop: int):
        self.slider.setRange(start, stop)
        self.spinbox.setRange(start, stop)

    def setStep(self, step: int):
        self.step = step
        self.spinbox.setSingleStep(step)

    def setToolTip(self, tooltip: str):
        self.slider.setToolTip(tooltip)

    def asTuple(self):
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
        self._setupUI()

    def _setupUI(self):
        self.setWindowTitle(ADDON_NAME)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)

        self.setLayout(self.createMainLayout())
        self.populateSliderRow()
        self.populateButtonRow()
        self.setupToolTips()
        self.setupLogic()
        self.setInitialValues()

    def createMainLayout(self):
        layout = QVBoxLayout()
        layout.addLayout(self.sliderRow)
        layout.addStretch()
        layout.addLayout(self.buttonRow)
        return layout

    def populateSliderRow(self):
        self.sliderRow.addWidget(
            self.createSlidersGroupBox(self.widthSlider, self.heightSlider, self.qualitySlider)
        )

    @staticmethod
    def createSlidersGroupBox(*sliders):
        gbox = QGroupBox("Settings")
        grid = QGridLayout()
        for y_index, slider in enumerate(sliders):
            grid.addWidget(QLabel(slider.title), y_index, 0)
            for x_index, widget in enumerate(slider.asTuple()):
                grid.addWidget(widget, y_index, x_index + 1)

        gbox.setLayout(grid)
        return gbox

    def populateButtonRow(self):
        for button in (self.okButton, self.cancelButton):
            button.setMinimumHeight(BUTTON_MIN_HEIGHT)
            self.buttonRow.addWidget(button)
        self.buttonRow.addStretch()

    def setupToolTips(self):
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
        self.widthSlider.setToolTip(side_tooltip % 'width')
        self.heightSlider.setToolTip(side_tooltip % 'height')
        self.qualitySlider.setToolTip(quality_tooltip)

    def setupLogic(self):
        for slider, limit in zip((self.widthSlider, self.heightSlider, self.qualitySlider), self.limits()):
            slider.setRange(0, limit)
            slider.setStep(SLIDER_STEP)

        self.okButton.clicked.connect(self.dialogAccept)
        self.cancelButton.clicked.connect(self.dialogReject)

    @staticmethod
    def limits() -> tuple:
        return config.get("max_image_width", 800), config.get("max_image_height", 600), 100

    def setInitialValues(self):
        self.widthSlider.setValue(config.get("image_width"))
        self.heightSlider.setValue(config.get("image_height"))
        self.qualitySlider.setValue(config.get("image_quality"))

    def dialogAccept(self):
        config["image_width"] = self.widthSlider.value()
        config["image_height"] = self.heightSlider.value()
        config["image_quality"] = self.qualitySlider.value()
        mw.addonManager.writeConfig(__name__, config)
        self.accept()

    def dialogReject(self):
        self.reject()


class SettingsMenuDialog(SettingsDialog):
    def __init__(self, *args, **kwargs):
        self.whenShowDialogComboBox = self.createWhenShowDialogComboBox()
        self.convertOnDragAndDropCheckBox = QCheckBox("Convert images on drag and drop")
        super(SettingsMenuDialog, self).__init__(*args, **kwargs)

    @staticmethod
    def createWhenShowDialogComboBox():
        combobox = QComboBox()
        for option in ShowOptions:
            combobox.addItem(option.value, option.name)
        return combobox

    def populateSliderRow(self):
        super(SettingsMenuDialog, self).populateSliderRow()
        self.sliderRow.addWidget(self.createAdditionalSettingsGroupBox())

    def createAdditionalSettingsGroupBox(self):
        def createInnerVbox():
            vbox = QVBoxLayout()
            vbox.addLayout(self.createShowSettingsLayout())
            vbox.addWidget(self.convertOnDragAndDropCheckBox)
            return vbox

        gbox = QGroupBox("Additional settings")
        gbox.setLayout(createInnerVbox())
        return gbox

    def setInitialValues(self):
        super(SettingsMenuDialog, self).setInitialValues()
        self.convertOnDragAndDropCheckBox.setChecked(config.get("drag_and_drop"))
        self.whenShowDialogComboBox.setCurrentIndex(ShowOptions.indexOf(config.get("show_settings")))

    def createShowSettingsLayout(self):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Show this dialog"))
        hbox.addWidget(self.whenShowDialogComboBox, 1)
        return hbox

    def showAboutDialog(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Love this add-on?")
        msg.setText(ABOUT_MSG)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def createHeartButton(self):
        heart_button = QPushButton()
        heart_button.setMinimumHeight(BUTTON_MIN_HEIGHT)
        heart_button.setToolTip("Support me")
        heart_button.setIcon(QIcon(os.path.join(ADDON_PATH, "icons", "heart.svg")))
        heart_button.setIconSize(QSize(ICON_SIDE_LEN, ICON_SIDE_LEN))
        heart_button.clicked.connect(self.showAboutDialog)
        return heart_button

    def populateButtonRow(self):
        super(SettingsMenuDialog, self).populateButtonRow()
        self.buttonRow.addWidget(self.createHeartButton())

    def dialogAccept(self):
        config["show_settings"] = self.whenShowDialogComboBox.currentData()
        config["drag_and_drop"] = self.convertOnDragAndDropCheckBox.isChecked()
        super(SettingsMenuDialog, self).dialogAccept()

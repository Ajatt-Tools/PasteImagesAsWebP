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

from ..consts import ADDON_PATH, ABOUT_MSG

BUTTON_MIN_HEIGHT = 29
ICON_SIDE_LEN = 17


class ShowOptions(Enum):
    always = "Always"
    toolbar = "On toolbar keypress"
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


class SettingsDialog(QDialog):
    def __init__(self, config, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)
        self.config = config
        self.cancelButton = QPushButton("Cancel")
        self.okButton = QPushButton("Ok")
        self.widthSlider = QSlider(Qt.Horizontal)
        self.widthSlider.title = "Width"
        self.heightSlider = QSlider(Qt.Horizontal)
        self.heightSlider.title = "Height"
        self.qualitySlider = QSlider(Qt.Horizontal)
        self.qualitySlider.title = "Quality"
        self.setWindowTitle("WebP settings")
        self.settingsLayout = QVBoxLayout()
        self.buttonRow = QHBoxLayout()
        self.setLayout(self.createMainLayout())
        self.populateSettingsLayout()
        self.createButtonRow()
        self.createLogic()
        self.setInitialValues()
        self.setMinimumWidth(320)

    def createMainLayout(self):
        layout = QVBoxLayout()
        layout.addLayout(self.settingsLayout)
        layout.addStretch()
        layout.addLayout(self.buttonRow)
        return layout

    def populateSettingsLayout(self):
        for slider in (self.widthSlider, self.heightSlider, self.qualitySlider):
            self.settingsLayout.addWidget(self.createSliderGroupBox(slider))

    @staticmethod
    def createSliderGroupBox(slider: QSlider):
        def createSliderHbox():
            hbox = QHBoxLayout()
            label = QLabel("0")
            hbox.addWidget(slider)
            hbox.addWidget(label)
            slider.valueChanged.connect(lambda val, lbl=label: lbl.setText(str(val)))
            return hbox

        gbox = QGroupBox(slider.title)
        gbox.setLayout(createSliderHbox())
        return gbox

    def createButtonRow(self):
        for button in (self.okButton, self.cancelButton):
            button.setMinimumHeight(BUTTON_MIN_HEIGHT)
            self.buttonRow.addWidget(button)
        self.buttonRow.addStretch()

    def dialogAccept(self):
        self.config["image_width"] = self.widthSlider.value()
        self.config["image_height"] = self.heightSlider.value()
        self.config["image_quality"] = self.qualitySlider.value()
        mw.addonManager.writeConfig(__name__, self.config)
        self.accept()

    def dialogReject(self):
        self.reject()

    def createLogic(self):
        for slider, limit in zip((self.widthSlider, self.heightSlider, self.qualitySlider), self.limits()):
            slider.setRange(0, limit)
            slider.setSingleStep(5)
            slider.setTickInterval(5)

        self.okButton.clicked.connect(self.dialogAccept)
        self.cancelButton.clicked.connect(self.dialogReject)

    @staticmethod
    def limits() -> tuple:
        return 800, 600, 100

    def setInitialValues(self):
        self.widthSlider.setValue(self.config.get("image_width"))
        self.heightSlider.setValue(self.config.get("image_height"))
        self.qualitySlider.setValue(self.config.get("image_quality"))


class SettingsMenuDialog(SettingsDialog):
    def __init__(self, *args, **kwargs):
        super(SettingsMenuDialog, self).__init__(*args, **kwargs)
        self.showDialogComboBox = QComboBox()
        self.convertOnDragAndDropCheckBox = QCheckBox("Convert images on drag and drop")
        self.createAdditionalSettingsGroupBox()
        self.populateShowDialogComboBox()
        self.setAdditionalInitialValues()

    def createShowSettingsLayout(self):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Show this dialog"))
        hbox.addWidget(self.showDialogComboBox, 1)
        return hbox

    def dialogAccept(self):
        self.config["show_settings"] = self.showDialogComboBox.currentData()
        self.config["drag_and_drop"] = self.convertOnDragAndDropCheckBox.isChecked()
        super(SettingsMenuDialog, self).dialogAccept()

    def setAdditionalInitialValues(self):
        self.convertOnDragAndDropCheckBox.setChecked(self.config.get("drag_and_drop"))
        self.showDialogComboBox.setCurrentIndex(ShowOptions.indexOf(self.config.get("show_settings")))

    def createAdditionalSettingsGroupBox(self):
        def createInnerVbox():
            vbox = QVBoxLayout()
            vbox.addLayout(self.createShowSettingsLayout())
            vbox.addWidget(self.convertOnDragAndDropCheckBox)
            return vbox

        gbox = QGroupBox("Additional settings")
        gbox.setLayout(createInnerVbox())
        self.settingsLayout.addWidget(gbox)

    def populateShowDialogComboBox(self):
        for option in ShowOptions:
            self.showDialogComboBox.addItem(option.value, option.name)

    def showAboutDialog(self):
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Love this add-on?")
        msg.setText(ABOUT_MSG)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def createHeartButton(self):
        heart_button = QPushButton()
        heart_button.setToolTip("Support me")
        heart_button.setIcon(QIcon(os.path.join(ADDON_PATH, "icons", "heart.svg")))
        heart_button.setIconSize(QSize(ICON_SIDE_LEN, ICON_SIDE_LEN))
        heart_button.clicked.connect(self.showAboutDialog)
        return heart_button

    def createButtonRow(self):
        super(SettingsMenuDialog, self).createButtonRow()
        self.buttonRow.addWidget(self.createHeartButton())

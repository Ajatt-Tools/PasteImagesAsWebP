from enum import Enum
from typing import List

from aqt import mw
from aqt.qt import *


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


class ConvertSettingsDialog(QDialog):
    def __init__(self, config, *args, **kwargs):
        super(ConvertSettingsDialog, self).__init__(*args, **kwargs)
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
        self.setLayout(self.createMainLayout())
        self.populateSettingsLayout()
        self.createLogic()
        self.setInitialValues()
        self.setMinimumWidth(320)

    def createMainLayout(self):
        layout = QVBoxLayout()
        layout.addLayout(self.settingsLayout)
        layout.addStretch()
        layout.addLayout(self.createButtonRow())
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
        layout = QHBoxLayout()
        for button in (self.okButton, self.cancelButton):
            layout.addWidget(button)
        layout.addStretch()
        return layout

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
            slider.setTickPosition(QSlider.TicksBelow)

        self.okButton.clicked.connect(self.dialogAccept)
        self.cancelButton.clicked.connect(self.dialogReject)

    @staticmethod
    def limits() -> List[int]:
        return [800, 600, 100]

    def setInitialValues(self):
        self.widthSlider.setValue(self.config.get("image_width"))
        self.heightSlider.setValue(self.config.get("image_height"))
        self.qualitySlider.setValue(self.config.get("image_quality"))


class ConvertSettingsMenuDialog(ConvertSettingsDialog):
    def __init__(self, *args, **kwargs):
        super(ConvertSettingsMenuDialog, self).__init__(*args, **kwargs)
        self.showDialogComboBox = QComboBox()
        self.convertOnDragAndDropCheckBox = QCheckBox("Convert images on drag and drop")
        self.settingsLayout.addWidget(self.createAdditionalSettingsGroupBox())
        self.populateShowDialogComboBox()
        self.setInitialAdditionalSettingsValues()

    def createShowSettingsLayout(self):
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Show this dialog"))
        hbox.addWidget(self.showDialogComboBox, 1)
        return hbox

    def dialogAccept(self):
        self.config["show_settings"] = self.showDialogComboBox.currentData()
        self.config["drag_and_drop"] = self.convertOnDragAndDropCheckBox.isChecked()
        super(ConvertSettingsMenuDialog, self).dialogAccept()

    def setInitialAdditionalSettingsValues(self):
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
        return gbox

    def populateShowDialogComboBox(self):
        for option in ShowOptions:
            self.showDialogComboBox.addItem(option.value, option.name)

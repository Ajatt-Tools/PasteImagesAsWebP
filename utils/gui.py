from typing import List

from aqt import mw
from aqt.qt import *


class ConvertSettingsDialog(QDialog):
    def __init__(self, parent, config, *args, **kwargs):
        super(ConvertSettingsDialog, self).__init__(parent, *args, **kwargs)
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
        self.showEachTimeCheckBox = QCheckBox("Show this dialog on each paste")
        self.setLayout(self.createMainLayout())
        self.createLogic()
        self.setInitialValues()
        self.setMinimumWidth(320)

    def createMainLayout(self):
        layout = QVBoxLayout()
        for slider in (self.widthSlider, self.heightSlider, self.qualitySlider):
            layout.addWidget(self.makeSliderGroupBox(slider))
        layout.addWidget(self.showEachTimeCheckBox)
        layout.addStretch()
        layout.addLayout(self.createButtonRow())
        return layout

    @staticmethod
    def makeSliderGroupBox(slider: QSlider):
        def makeSliderHbox():
            hbox = QHBoxLayout()
            label = QLabel("0")
            hbox.addWidget(slider)
            hbox.addWidget(label)
            slider.valueChanged.connect(lambda val, lbl=label: lbl.setText(str(val)))
            return hbox

        gbox = QGroupBox(slider.title)
        gbox.setLayout(makeSliderHbox())
        return gbox

    def createButtonRow(self):
        layout = QHBoxLayout()
        for button in (self.okButton, self.cancelButton):
            layout.addWidget(button)
        layout.addStretch()
        return layout

    def createLogic(self):
        def dialogAccept():
            self.config["width"] = self.widthSlider.value()
            self.config["height"] = self.heightSlider.value()
            self.config["quality"] = self.qualitySlider.value()
            self.config["dialog_on_paste"] = self.showEachTimeCheckBox.isChecked()
            mw.addonManager.writeConfig(__name__, self.config)
            self.accept()

        def dialogReject():
            self.reject()

        for slider, limit in zip((self.widthSlider, self.heightSlider, self.qualitySlider), self.limits()):
            slider.setRange(0, limit)
            slider.setSingleStep(5)
            slider.setTickInterval(5)
            slider.setTickPosition(QSlider.TicksBelow)

        self.okButton.clicked.connect(dialogAccept)
        self.cancelButton.clicked.connect(dialogReject)
        self.showEachTimeCheckBox.setChecked(self.config.get("dialog_on_paste"))

    @staticmethod
    def limits() -> List[int]:
        return [800, 600, 100]

    def setInitialValues(self):
        self.widthSlider.setValue(self.config.get("width"))
        self.heightSlider.setValue(self.config.get("height"))
        self.qualitySlider.setValue(self.config.get("quality"))

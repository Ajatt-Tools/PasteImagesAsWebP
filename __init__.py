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


import json
import subprocess
import time
from distutils.spawn import find_executable
from tempfile import mkstemp
from typing import List

from anki.hooks import addHook
from aqt import mw
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

addon_path = os.path.dirname(__file__)


######################################################################
# Utils
######################################################################

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func

    return decorate


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__) or dict()
    cfg['show_context_menu_entry']: bool = cfg.get('show_context_menu_entry', True)
    cfg['show_editor_button']: bool = cfg.get('show_editor_button', True)
    cfg['shortcut']: str = cfg.get('shortcut', "Ctrl+Meta+v")
    cfg['width']: int = cfg.get('width', 0)
    cfg['height']: int = cfg.get('height', 200)
    cfg['quality']: str = cfg.get('quality', 20)
    cfg['dialog_on_paste']: bool = cfg.get('dialog_on_paste', True)

    return cfg


def find_cwebp():
    exe = find_executable('cwebp')
    if exe is None:
        # https://developers.google.com/speed/webp/download
        support_dir = "support"
        if isWin:
            exe = os.path.join(addon_path, support_dir, "cwebp.exe")
        else:
            exe = os.path.join(addon_path, support_dir, "cwebp")
            os.chmod(exe, 0o755)
    return exe


def apply_resize_args(args: list):
    width = config.get('width')
    height = config.get('height')
    if not (width == 0 and height == 0):
        args.extend(['-resize', str(width), str(height)])
    return args


@static_vars(cwebp=find_cwebp())
def convert_file(source_path, destination_path):
    args = [
        convert_file.cwebp,
        source_path,
        '-short',
        '-mt',
        '-pass', '10',
        '-af',
        '-blend_alpha', '0xffffff',
        '-m', '6',
        '-q', str(config.get('quality')),
        '-o', destination_path
    ]
    args = apply_resize_args(args)

    try:
        subprocess.check_output(args)
    except subprocess.CalledProcessError as ex:
        print(f"cwebp failed.")
        print(f"\texit code = {ex.returncode}")
        print(f"\toutput = {ex.output}")
        return False
    return True


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()

    if not mime.hasImage():
        return

    fd, tmp_filepath = mkstemp()

    image: QImage = mime.imageData()
    if image.save(tmp_filepath, 'png') is True:
        if config.get("dialog_on_paste") is True:
            dlg = ConvertSettingsDialog(editor.parentWindow)
            if not dlg.exec_():
                # the user pressed `Cancel`.
                return
        out_filename: str = str(int(time.time())) + '.webp'
        out_filepath: str = os.path.join(mw.col.media.dir(), out_filename)
        if convert_file(tmp_filepath, out_filepath) is True:
            image_html = f'<img src="{out_filename}">'
            editor.web.eval("""setFormat("insertHtml", %s);""" % json.dumps(image_html))  # calls document.execCommand
            filesize_kib = str(os.stat(out_filepath).st_size / 1024)
            tooltip(f"Image added. File size: {filesize_kib[:filesize_kib.find('.') + 3]} KiB.", period=5000)
        else:
            tooltip("cwebp failed.")
    os.close(fd)
    os.remove(tmp_filepath)


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.NativeText)


######################################################################
# Settings dialog
######################################################################

class ConvertSettingsDialog(QDialog):
    def __init__(self, parent, *args, **kwargs):
        super(ConvertSettingsDialog, self).__init__(parent, *args, **kwargs)

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
            label = QLabel()
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
            config["width"] = self.widthSlider.value()
            config["height"] = self.heightSlider.value()
            config["quality"] = self.qualitySlider.value()
            config["dialog_on_paste"] = self.showEachTimeCheckBox.isChecked()
            mw.addonManager.writeConfig(__name__, config)
            self.accept()

        def dialogReject():
            self.reject()

        for slider, limit in zip((self.widthSlider, self.heightSlider, self.qualitySlider), self.limits()):
            slider.setRange(0, limit)
            slider.setSingleStep(5)
            slider.setTickPosition(QSlider.TicksBelow)

        self.okButton.clicked.connect(dialogAccept)
        self.cancelButton.clicked.connect(dialogReject)
        self.showEachTimeCheckBox.setChecked(config.get("dialog_on_paste"))

    @staticmethod
    def limits() -> List[int]:
        return [800, 600, 100]

    def setInitialValues(self):
        self.widthSlider.setValue(config.get("width"))
        self.heightSlider.setValue(config.get("height"))
        self.qualitySlider.setValue(config.get("quality"))


######################################################################
# Main
######################################################################

def setup_mainwindow_menu():
    """
    setup menu in anki
    """

    def open_settings():
        dialog = ConvertSettingsDialog(mw)
        dialog.exec_()

    action = QAction("WebP settings", mw)
    action.triggered.connect(open_settings)
    mw.form.menuTools.addAction(action)


def setup_editor_menus():
    shortcut: str = config.get("shortcut")
    action_tooltip: str = "Paste as webp"
    if shortcut:
        action_tooltip += f" ({key_to_str(shortcut)})"

    if config.get("show_context_menu_entry") is True:
        def add_context_menu_item(webview: EditorWebView, menu: QMenu):
            editor = webview.editor
            a: QAction = menu.addAction(action_tooltip)
            a.triggered.connect(lambda _, e=editor: insert_webp(e))

        addHook('EditorWebView.contextMenuEvent', add_context_menu_item)

    if config.get("show_editor_button") is True:
        def add_editor_button(buttons, editor):
            b = editor.addButton(
                os.path.join(addon_path, "webp_icon.png"),
                "paste_webp_button",
                lambda e=editor: insert_webp(e),
                tip=action_tooltip,
                keys=shortcut
            )
            buttons.extend([b])
            return buttons

        addHook("setupEditorButtons", add_editor_button)

    elif shortcut:
        def add_editor_shortcut(cuts, self):
            cuts.append((shortcut, lambda e=self: insert_webp(e)))

        addHook("setupEditorShortcuts", add_editor_shortcut)


config = get_config()
setup_editor_menus()
setup_mainwindow_menu()

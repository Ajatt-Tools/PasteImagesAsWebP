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

from anki.hooks import wrap
from aqt import mw, gui_hooks
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

from .consts import ADDON_PATH
from .utils.gui import SettingsDialog, ShowOptions, SettingsMenuDialog
from .utils.imagehelper import save_image
from .utils.tempfile import TempFile


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
    cfg['shortcut']: str = cfg.get('shortcut', 'Ctrl+Meta+v')
    cfg['image_width']: int = cfg.get('image_width', 0)
    cfg['image_height']: int = cfg.get('image_height', 200)
    cfg['image_quality']: str = cfg.get('image_quality', 20)
    cfg['show_settings']: str = cfg.get('show_settings', 'toolbar')
    cfg["drag_and_drop"]: bool = cfg.get('drag_and_drop', True)

    return cfg


def find_cwebp():
    exe = find_executable('cwebp')
    if exe is None:
        # https://developers.google.com/speed/webp/download
        support_dir = "support"
        if isWin:
            exe = os.path.join(ADDON_PATH, support_dir, "cwebp.exe")
        else:
            exe = os.path.join(ADDON_PATH, support_dir, "cwebp")
            os.chmod(exe, 0o755)
    return exe


def apply_resize_args(args: list):
    width = config.get('image_width')
    height = config.get('image_height')
    if not (width == 0 and height == 0):
        args.extend(['-resize', str(width), str(height)])
    return args


def make_webp_filename(target_dir_path: str):
    """Returns a unique (filename, filepath) for the new webp image"""

    def new_filename() -> str:
        import random
        return f"paste_{int(time.time())}{random.randint(100, 999)}.webp"

    def make_full_path(name) -> str:
        return os.path.join(target_dir_path, name)

    out_filename: str = new_filename()
    while os.path.isfile(make_full_path(out_filename)):
        out_filename = new_filename()

    return out_filename, make_full_path(out_filename)


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
        '-q', str(config.get('image_quality')),
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


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.NativeText)


def tooltip_filesize(filepath):
    filesize_kib = str(os.stat(filepath).st_size / 1024)
    tooltip(f"Image added. File size: {filesize_kib[:filesize_kib.find('.') + 3]} KiB.", period=5000)


def decide_show_settings(dialog_parent, parent_action: ShowOptions):
    if config.get("show_settings") == ShowOptions.always or config.get("show_settings") == parent_action:
        dlg = SettingsDialog(config, dialog_parent)
        return dlg.exec_()
    return True


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()

    with TempFile() as tmp_file:
        if not save_image(tmp_file.path(), mime):
            tooltip("Couldn't save the image.")
            return

        if not decide_show_settings(editor.parentWindow, ShowOptions.toolbar):
            tooltip("Canceled.")
            return

        out_filename, out_filepath = make_webp_filename(mw.col.media.dir())
        if convert_file(tmp_file.path(), out_filepath) is True:
            image_html = f'<img src="{out_filename}">'
            editor.web.eval(
                """setFormat("insertHtml", %s);""" % json.dumps(image_html)  # calls document.execCommand
            )
            tooltip_filesize(out_filepath)
        else:
            tooltip("cwebp failed.")


def process_mime(editor: EditorWebView, mime: QMimeData, *args, _old):
    """Called when you paste anything in Anki"""

    if config.get("drag_and_drop") is False:
        return _old(editor, mime, *args)

    p = editor.editor.web.mapFromGlobal(QCursor.pos())

    with TempFile() as tmp_file:
        if not save_image(tmp_file.path(), mime):
            return _old(editor, mime, *args)

        if not decide_show_settings(editor.parent(), ShowOptions.drag_and_drop):
            tooltip("Canceled.")
            return _old(editor, mime, *args)

        out_filename, out_filepath = make_webp_filename(mw.col.media.dir())

        if convert_file(tmp_file, out_filepath) is True:
            tooltip_filesize(out_filepath)
            mime = QMimeData()  # erase old data from mime

            def pasteField(_):
                editor.editor.web.eval(
                    "pasteHTML(%s);" % json.dumps(f'<img src="{out_filename}">')
                )

            editor.editor.web.evalWithCallback(f"focusIfField({p.x()}, {p.y()});", pasteField)
        else:
            tooltip("cwebp failed.")

    return _old(editor, mime, *args)


######################################################################
# Main
######################################################################

def setup_mainwindow_menu():
    """
    setup menu in anki
    """
    tools_menu = mw.form.menuTools

    def open_settings():
        dialog = SettingsMenuDialog(config, tools_menu)
        dialog.exec_()

    action = QAction("WebP settings", tools_menu)
    action.triggered.connect(open_settings)
    tools_menu.addAction(action)


def wrap_process_mime():
    EditorWebView._processMime = wrap(EditorWebView._processMime, process_mime, 'around')


def setup_menus():
    setup_mainwindow_menu()
    wrap_process_mime()
    shortcut: str = config.get("shortcut")
    action_tooltip: str = "Paste as WebP" if not shortcut else f"Paste as WebP ({key_to_str(shortcut)})"

    if config.get("show_context_menu_entry") is True:
        def add_context_menu_item(webview: EditorWebView, menu: QMenu):
            editor = webview.editor
            a: QAction = menu.addAction(action_tooltip)
            a.triggered.connect(lambda _, e=editor: insert_webp(e))

        gui_hooks.editor_will_show_context_menu.append(add_context_menu_item)

    if config.get("show_editor_button") is True:
        def add_editor_button(buttons, editor):
            b = editor.addButton(
                os.path.join(ADDON_PATH, "icons", "webp.png"),
                "paste_webp_button",
                lambda e=editor: insert_webp(e),
                tip=action_tooltip,
                keys=shortcut
            )
            buttons.extend([b])
            return buttons

        gui_hooks.editor_did_init_buttons.append(add_editor_button)

    elif shortcut:
        def add_editor_shortcut(cuts, self):
            cuts.append((shortcut, lambda e=self: insert_webp(e)))

        gui_hooks.editor_did_init_shortcuts.append(add_editor_shortcut)


config = get_config()
setup_menus()

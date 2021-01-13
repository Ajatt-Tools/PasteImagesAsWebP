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
from typing import Optional

from anki.hooks import wrap
from aqt import mw, gui_hooks
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

from .config import config
from .consts import ADDON_PATH
from .utils import webp
from .utils.gui import SettingsDialog, ShowOptions, SettingsMenuDialog
from .utils.imagehelper import save_image, image_candidates
from .utils.tempfile import TempFile


######################################################################
# Utils
######################################################################


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.NativeText)


def tooltip_filesize(filepath) -> None:
    filesize_kib = str(os.stat(filepath).st_size / 1024)
    tooltip(f"Image added. File size: {filesize_kib[:filesize_kib.find('.') + 3]} KiB.", period=5000)


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=f'<img src="{image_filename}">', internal=True)


class ImageProcessor:
    def __init__(self, parent: QWidget, caller_action: ShowOptions):
        self.dialog_parent: QWidget = parent
        self.parent_action: ShowOptions = caller_action
        self.image: Optional[QImage] = None

    def shouldShowSettings(self) -> bool:
        return config.get("show_settings") == ShowOptions.always or config.get("show_settings") == self.parent_action

    def decideShowSettings(self) -> int:
        if self.shouldShowSettings() is True:
            dlg = SettingsDialog(self.dialog_parent)
            return dlg.exec_()
        return QDialog.Accepted

    def saveImage(self, tmp_path: str, mime: QMimeData) -> bool:
        for image in image_candidates(mime):
            if image and image.save(tmp_path, 'png') is True:
                # self.image = image  TODO
                break
        else:
            return False

        return True

    def saveAsWebP(self, mime: QMimeData) -> (str, str):
        with TempFile() as tmp_file:
            if save_image(tmp_file.path(), mime) is False:
                raise RuntimeError("Couldn't save the image.")

            if self.decideShowSettings() == QDialog.Rejected:
                raise Warning("Canceled.")

            out_filename, out_filepath = webp.construct_filename(mw.col.media.dir())

            if webp.convert_file(tmp_file.path(), out_filepath) is False:
                raise RuntimeError("cwebp failed")

        return out_filename, out_filepath


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    w = ImageProcessor(editor.parentWindow, ShowOptions.toolbar)
    try:
        out_filename, out_filepath = w.saveAsWebP(mime)
        insert_image_html(editor, out_filename)
        tooltip_filesize(out_filepath)
    except Exception as ex:
        tooltip(ex)


def drop_event(editor: EditorWebView, event, _old):
    if config.get("drag_and_drop") is False:
        # the feature is disabled by the user
        return _old(editor, event)

    if event.source():
        # don't filter html from other fields
        return _old(editor, event)

    # grab cursor position before it's moved by the user
    p = editor.editor.web.mapFromGlobal(QCursor.pos())

    w = ImageProcessor(editor.window(), ShowOptions.drag_and_drop)
    try:
        out_filename, out_filepath = w.saveAsWebP(event.mimeData())

        def pasteField(_):
            insert_image_html(editor.editor, out_filename)
            editor.activateWindow()  # Fix for windows users

        editor.editor.web.evalWithCallback(f"focusIfField({p.x()}, {p.y()});", pasteField)
        tooltip_filesize(out_filepath)
    except Warning as ex:
        tooltip(ex)
    except RuntimeError as ex:
        tooltip(ex)
        return _old(editor, event)


def paste_event(editor: EditorWebView, _old):
    if config.get("copy_paste") is False:
        # the feature is disabled by the user
        return _old(editor)

    mime: QMimeData = mw.app.clipboard().mimeData()

    if mime.html().startswith("<!--anki-->"):
        # no filtering required for internal pastes
        return _old(editor)

    w = ImageProcessor(editor.window(), ShowOptions.toolbar)
    try:
        out_filename, out_filepath = w.saveAsWebP(mime)
        insert_image_html(editor.editor, out_filename)
        tooltip_filesize(out_filepath)
    except Warning as ex:
        tooltip(ex)
    except RuntimeError as ex:
        tooltip(ex)
        return _old(editor)


######################################################################
# Main
######################################################################


def setup_mainwindow_menu():
    """
    setup menu in anki
    """
    tools_menu = mw.form.menuTools

    def open_settings():
        dialog = SettingsMenuDialog(tools_menu)
        dialog.exec_()

    action = QAction("WebP settings", tools_menu)
    action.triggered.connect(open_settings)
    tools_menu.addAction(action)


def wrap_events():
    EditorWebView.dropEvent = wrap(EditorWebView.dropEvent, drop_event, 'around')
    EditorWebView.onPaste = wrap(EditorWebView.onPaste, paste_event, 'around')


def setup_menus():
    setup_mainwindow_menu()
    wrap_events()
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


setup_menus()

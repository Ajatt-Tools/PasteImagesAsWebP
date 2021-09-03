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
from typing import List, Tuple

from anki.hooks import wrap
from aqt import mw, gui_hooks
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

from .ajt_common import menu_root_entry
from .config import config
from .consts import ADDON_PATH
from .utils import bulkconvert
from .utils.gui import ShowOptions, SettingsMenuDialog
from .utils.webp import ImageConverter, CanceledPaste, InvalidInput


######################################################################
# Utils
######################################################################


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.NativeText)


def tooltip_filesize(filepath: os.PathLike) -> None:
    filesize_kib = str(os.stat(filepath).st_size / 1024)
    tooltip(f"Image added. File size: {filesize_kib[:filesize_kib.find('.') + 3]} KiB.", period=5000)


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=f'<img src="{image_filename}">', internal=True)


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    w = ImageConverter(editor, ShowOptions.menus)
    try:
        w.convert(mime)
        insert_image_html(editor, w.filepath.name)
        tooltip_filesize(w.filepath)
    except Exception as ex:
        tooltip(str(ex))


def drop_event(editor: EditorWebView, event: QDropEvent, _old: Callable):
    if config.get("drag_and_drop") is False:
        # the feature is disabled by the user
        return _old(editor, event)

    if event.source():
        # don't filter html from other fields
        return _old(editor, event)

    # grab cursor position before it's moved by the user
    p = editor.editor.web.mapFromGlobal(QCursor.pos())

    w = ImageConverter(editor.editor, ShowOptions.drag_and_drop)
    try:
        w.convert(event.mimeData())

        def paste_field(_):
            insert_image_html(editor.editor, w.filepath.name)
            editor.activateWindow()  # Fix for windows users

        editor.editor.web.evalWithCallback(f"focusIfField({p.x()}, {p.y()});", paste_field)
        tooltip_filesize(w.filepath)
    except InvalidInput:
        return _old(editor, event)
    except CanceledPaste as ex:
        tooltip(str(ex))
    except RuntimeError as ex:
        tooltip(str(ex))
        return _old(editor, event)
    except FileNotFoundError:
        tooltip("File not found.")
        return _old(editor, event)


def has_local_file(mime: QMimeData) -> bool:
    for url in mime.urls():
        if url.isLocalFile():
            return True
    return False


def paste_event(editor: EditorWebView, _old: Callable):
    if config.get("copy_paste") is False:
        # the feature is disabled by the user
        return _old(editor)

    mime: QMimeData = mw.app.clipboard().mimeData()

    if mime.html().startswith("<!--anki-->"):
        # no filtering required for internal pastes
        return _old(editor)

    if not (mime.hasImage() or has_local_file(mime)):
        # no image was copied
        return _old(editor)

    w = ImageConverter(editor.editor, ShowOptions.menus)
    try:
        w.convert(mime)
        insert_image_html(editor.editor, w.filepath.name)
        tooltip_filesize(w.filepath)
    except CanceledPaste as ex:
        tooltip(str(ex))
    except InvalidInput:
        return _old(editor)
    except RuntimeError as ex:
        tooltip(str(ex))
        return _old(editor)
    except FileNotFoundError:
        tooltip("File not found.")
        return _old(editor)


######################################################################
# Main
######################################################################


def setup_mainwindow_menu():
    """
    setup menu in anki
    """
    root_menu = menu_root_entry()

    def open_settings():
        dialog = SettingsMenuDialog(mw)
        dialog.exec_()

    action = QAction("WebP settings...", root_menu)
    action.triggered.connect(open_settings)
    root_menu.addAction(action)


def custom_decorate(old: Callable, new: Callable):
    """Avoids crash by discarding args[1](=False) when called from context menu."""

    # https://forums.ankiweb.net/t/investigating-an-ambigous-add-on-error/12846
    def wrapper(*args):
        return new(args[0], _old=old)

    return wrapper


def setup_editor_menus():
    def wrap_events():
        EditorWebView.dropEvent = wrap(EditorWebView.dropEvent, drop_event, 'around')
        EditorWebView.onPaste = custom_decorate(EditorWebView.onPaste, paste_event)

    def add_context_menu_item(webview: EditorWebView, menu: QMenu):
        editor = webview.editor
        a: QAction = menu.addAction(action_tooltip)
        a.triggered.connect(lambda _, e=editor: insert_webp(e))

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

    def add_editor_shortcut(cuts: List[Tuple], self: Editor):
        cuts.append((shortcut, lambda e=self: insert_webp(e)))

    wrap_events()
    shortcut: str = config.get("shortcut")
    action_tooltip: str = "Paste as WebP" if not shortcut else f"Paste as WebP ({key_to_str(shortcut)})"

    if config.get("show_context_menu_entry") is True:
        gui_hooks.editor_will_show_context_menu.append(add_context_menu_item)

    if config.get("show_editor_button") is True:
        gui_hooks.editor_did_init_buttons.append(add_editor_button)
    elif shortcut:
        gui_hooks.editor_did_init_shortcuts.append(add_editor_shortcut)


setup_mainwindow_menu()
setup_editor_menus()
bulkconvert.init()

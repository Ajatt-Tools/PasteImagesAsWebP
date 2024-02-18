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

from aqt import mw, gui_hooks
from aqt.editor import EditorWebView

from .ajt_common.about_menu import menu_root_entry
from .common import *
from .config import config
from .consts import ADDON_PATH
from .gui import SettingsMenuDialog
from .utils.show_options import ShowOptions
from .webp import OnPasteConverter


def setup_mainwindow_menu():
    """
    setup menu in anki
    """
    root_menu = menu_root_entry()

    def open_settings():
        dialog = SettingsMenuDialog(mw)
        dialog.exec()

    action = QAction("WebP Options...", root_menu)
    qconnect(action.triggered, open_settings)
    root_menu.addAction(action)


def action_tooltip():
    return (
        "Paste as WebP"
        if not config['shortcut']
        else f"Paste as WebP ({key_to_str(config['shortcut'])})"
    )


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    w = OnPasteConverter(editor, editor.note, ShowOptions.toolbar)
    try:
        w.convert_mime(mime)
        insert_image_html(editor, w.filename)
        w.result_tooltip(w.filepath)
    except Exception as ex:
        w.tooltip(ex)


def on_editor_will_show_context_menu(webview: EditorWebView, menu: QMenu):
    if config.get("show_context_menu_entry") is True:
        action: QAction = menu.addAction(action_tooltip())
        qconnect(action.triggered, lambda _, e=webview.editor: insert_webp(e))


def on_editor_did_init_buttons(buttons: list[str], editor: Editor):
    """
    Append a new editor button if it's enabled.
    """
    if config["show_editor_button"] is True:
        buttons.append(editor.addButton(
            icon=os.path.join(ADDON_PATH, "icons", "webp.png"),
            cmd="ajt__paste_webp_button",
            func=lambda e=editor: insert_webp(e),
            tip=action_tooltip(),
            keys=config['shortcut'] or None,
        ))


def on_editor_did_init_shortcuts(cuts: list[tuple], self: Editor):
    """
    Add keyboard shortcut if it is set and if editor button is disabled.
    If editor button is enabled, it has its own keyboard shortcut.
    """
    if config["show_editor_button"] is False and config['shortcut']:
        cuts.append((config['shortcut'], lambda e=self: insert_webp(e)))


def setup_editor_menus():
    gui_hooks.editor_did_init_buttons.append(on_editor_did_init_buttons)
    gui_hooks.editor_did_init_shortcuts.append(on_editor_did_init_shortcuts)
    gui_hooks.editor_will_show_context_menu.append(on_editor_will_show_context_menu)


def init():
    setup_mainwindow_menu()
    setup_editor_menus()

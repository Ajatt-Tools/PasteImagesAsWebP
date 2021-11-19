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

from aqt import mw, gui_hooks
from aqt.editor import EditorWebView

from .ajt_common import menu_root_entry
from .common import *
from .config import config
from .consts import ADDON_PATH
from .utils.gui import SettingsMenuDialog


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


def setup_editor_menus():
    shortcut: str = config.get("shortcut")
    action_tooltip: str = "Paste as WebP" if not shortcut else f"Paste as WebP ({key_to_str(shortcut)})"

    def add_editor_shortcut(cuts: List[Tuple], self: Editor):
        cuts.append((shortcut, lambda e=self: insert_webp(e)))

    def add_context_menu_item(webview: EditorWebView, menu: QMenu):
        a: QAction = menu.addAction(action_tooltip)
        a.triggered.connect(lambda _, e=webview.editor: insert_webp(e))

    def add_editor_button(buttons, editor):
        b = editor.addButton(
            os.path.join(ADDON_PATH, "icons", "webp.png"),
            "paste_webp_button",
            lambda e=editor: insert_webp(e),
            tip=action_tooltip,
            keys=shortcut
        )
        buttons.append(b)
        return buttons

    if config.get("show_context_menu_entry") is True:
        gui_hooks.editor_will_show_context_menu.append(add_context_menu_item)

    if config.get("show_editor_button") is True:
        gui_hooks.editor_did_init_buttons.append(add_editor_button)
    elif shortcut:
        gui_hooks.editor_did_init_shortcuts.append(add_editor_shortcut)


def init():
    setup_mainwindow_menu()
    setup_editor_menus()

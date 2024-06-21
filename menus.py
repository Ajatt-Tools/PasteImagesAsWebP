# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt import mw, gui_hooks
from aqt.editor import EditorWebView

from .ajt_common.about_menu import menu_root_entry
from .common import *
from .config import config
from .consts import ADDON_PATH
from .gui import SettingsMenuDialog
from .utils.show_options import ShowOptions
from .image_conversion import OnPasteConverter


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


def insert_webp(editor: Editor, source: ShowOptions):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    w = OnPasteConverter(editor, editor.note, source)
    try:
        w.convert_mime(mime)
        insert_image_html(editor, w.filename)
        w.result_tooltip(w.filepath)
    except Exception as ex:
        w.tooltip(ex)


def on_editor_will_show_context_menu(webview: EditorWebView, menu: QMenu):
    if config.get("show_context_menu_entry") is True:
        action: QAction = menu.addAction(action_tooltip())
        qconnect(action.triggered, lambda _, e=webview.editor: insert_webp(e, source=ShowOptions.paste))


def on_editor_did_init_buttons(buttons: list[str], editor: Editor):
    """
    Append a new editor button if it's enabled.
    """
    if config["show_editor_button"] is True:
        buttons.append(editor.addButton(
            icon=os.path.join(ADDON_PATH, "icons", "webp.png"),
            cmd="ajt__paste_webp_button",
            func=lambda e=editor: insert_webp(e, source=ShowOptions.toolbar),
            tip=action_tooltip(),
            keys=config['shortcut'] or None,
        ))


def on_editor_did_init_shortcuts(cuts: list[tuple], self: Editor):
    """
    Add keyboard shortcut if it is set and if editor button is disabled.
    If editor button is enabled, it has its own keyboard shortcut.
    """
    if config["show_editor_button"] is False and config['shortcut']:
        cuts.append((config['shortcut'], lambda e=self: insert_webp(e, source=ShowOptions.paste)))


def setup_editor_menus():
    gui_hooks.editor_did_init_buttons.append(on_editor_did_init_buttons)
    gui_hooks.editor_did_init_shortcuts.append(on_editor_did_init_shortcuts)
    gui_hooks.editor_will_show_context_menu.append(on_editor_will_show_context_menu)


def init():
    setup_mainwindow_menu()
    setup_editor_menus()

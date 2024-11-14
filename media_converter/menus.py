# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import os.path

from aqt import gui_hooks, mw
from aqt.editor import EditorWebView

from .ajt_common.about_menu import menu_root_entry
from .common import *
from .config import config
from .consts import ADDON_FULL_NAME, ADDON_NAME, ADDON_PATH
from .file_converters.file_converter import FFmpegNotFoundError
from .file_converters.image_converter import ffmpeg_not_found_dialog
from .file_converters.on_paste_converter import OnPasteConverter
from .gui import SettingsMenuDialog
from .utils.show_options import ShowOptions


def setup_mainwindow_menu():
    """
    setup menu in anki
    """
    root_menu = menu_root_entry()

    def open_settings():
        dialog = SettingsMenuDialog(mw)
        dialog.exec()

    action = QAction(f"{ADDON_NAME} Options...", root_menu)
    qconnect(action.triggered, open_settings)
    root_menu.addAction(action)


def action_tooltip():
    return (
        f"{ADDON_FULL_NAME}: Paste"
        if not config["shortcut"]
        else f"{ADDON_FULL_NAME}: Paste ({key_to_str(config['shortcut'])})"
    )


def convert_and_insert(editor: Editor, source: ShowOptions):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    conv = OnPasteConverter(editor, source)
    try:
        new_file_path = conv.convert_mime(mime)
    except FFmpegNotFoundError:
        ffmpeg_not_found_dialog()
    except Exception as ex:
        conv.tooltip(ex)
    else:
        insert_image_html(editor, os.path.basename(new_file_path))
        conv.result_tooltip(new_file_path)


def on_editor_will_show_context_menu(webview: EditorWebView, menu: QMenu):
    if config.get("show_context_menu_entry") is True:
        action: QAction = menu.addAction(action_tooltip())
        qconnect(action.triggered, lambda _, e=webview.editor: convert_and_insert(e, source=ShowOptions.paste))


def on_editor_did_init_buttons(buttons: list[str], editor: Editor):
    """
    Append a new editor button if it's enabled.
    """
    if config["show_editor_button"] is True:
        buttons.append(
            editor.addButton(
                icon=os.path.join(ADDON_PATH, "icons", "webp.png"),
                cmd=f"ajt__{ADDON_FULL_NAME.lower().replace(' ', '_')}_button",
                func=functools.partial(convert_and_insert, editor=editor, source=ShowOptions.toolbar),
                tip=action_tooltip(),
                keys=config["shortcut"] or None,
            )
        )


def on_editor_did_init_shortcuts(cuts: list[tuple], self: Editor):
    """
    Add keyboard shortcut if it is set and if editor button is disabled.
    If editor button is enabled, it has its own keyboard shortcut.
    """
    if config["show_editor_button"] is False and config["shortcut"]:
        cuts.append((config["shortcut"], lambda e=self: convert_and_insert(e, source=ShowOptions.paste)))


def setup_editor_menus():
    gui_hooks.editor_did_init_buttons.append(on_editor_did_init_buttons)
    gui_hooks.editor_did_init_shortcuts.append(on_editor_did_init_shortcuts)
    gui_hooks.editor_will_show_context_menu.append(on_editor_will_show_context_menu)


def init() -> None:
    setup_mainwindow_menu()
    setup_editor_menus()

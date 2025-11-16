# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import os.path

from aqt import gui_hooks, mw
from aqt.editor import Editor, EditorWebView
from aqt.qt import *

from .ajt_common.about_menu import menu_root_entry
from .common import insert_image_html, key_to_str
from .config import MediaConverterConfig
from .consts import ADDON_FULL_NAME, ADDON_NAME, ADDON_PATH
from .dialogs.main_settings_dialog import AnkiMainSettingsDialog
from .file_converters.file_converter import FFmpegNotFoundError
from .file_converters.image_converter import ffmpeg_not_found_dialog
from .file_converters.on_paste_converter import (
    TEMP_IMAGE_FORMAT,
    OnPasteConverter,
    mime_to_image_file,
)
from .media_deduplication.anki_collection_op import run_media_deduplication
from .utils.show_options import ShowOptions
from .utils.temp_file import TempFile


def setup_mainwindow_menu() -> None:
    """
    setup menu in anki
    """
    from .config import config

    root_menu = menu_root_entry()

    def open_settings():
        dialog = AnkiMainSettingsDialog(config, mw)
        dialog.show()

    action = QAction(f"{ADDON_NAME} Options...", root_menu)
    qconnect(action.triggered, open_settings)
    root_menu.addAction(action)

    action = QAction(f"Deduplicate media...", root_menu)
    qconnect(action.triggered, run_media_deduplication)
    root_menu.addAction(action)


def convert_and_insert(editor: Editor, source: ShowOptions) -> None:
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    conv = OnPasteConverter(editor, source)
    with TempFile(suffix=f".{TEMP_IMAGE_FORMAT}") as tmp_file:
        if to_convert := mime_to_image_file(mime, tmp_file.path()):
            try:
                new_file_path = conv.convert_mime(to_convert)
            except FFmpegNotFoundError:
                ffmpeg_not_found_dialog()
            except FileNotFoundError:
                conv.tooltip("File not found.")
            except Exception as ex:
                conv.tooltip(ex)
            else:
                # File has been converted.
                insert_image_html(editor, os.path.basename(new_file_path))
                conv.result_tooltip(new_file_path)


class Menus:
    _config: MediaConverterConfig

    def __init__(self, config: MediaConverterConfig) -> None:
        self._config = config

    def on_editor_did_init_buttons(self, buttons: list[str], editor: Editor) -> None:
        """
        Append a new editor button if it's enabled.
        """
        if self._config.show_editor_button:
            buttons.append(
                editor.addButton(
                    icon=os.path.join(ADDON_PATH, "icons", "webp.png"),
                    cmd=f"ajt__{ADDON_FULL_NAME.lower().replace(' ', '_')}_button",
                    func=functools.partial(convert_and_insert, source=ShowOptions.toolbar),
                    tip=self._action_tooltip(),
                    keys=self._config.shortcut or None,
                )
            )

    def _action_tooltip(self) -> str:
        return (
            f"{ADDON_FULL_NAME}: Paste"
            if not self._config.shortcut
            else f"{ADDON_FULL_NAME}: Paste ({key_to_str(self._config.shortcut)})"
        )

    def on_editor_did_init_shortcuts(self, cuts: list[tuple], editor: Editor) -> None:
        """
        Add keyboard shortcut if it is set and if editor button is disabled.
        If editor button is enabled, it has its own keyboard shortcut.
        """
        if not self._config.show_editor_button and self._config.shortcut:
            cuts.append(
                (self._config.shortcut, functools.partial(convert_and_insert, editor=editor, source=ShowOptions.paste))
            )

    def on_editor_will_show_context_menu(self, webview: EditorWebView, menu: QMenu) -> None:
        if self._config.show_context_menu_entry:
            action: QAction = menu.addAction(self._action_tooltip())
            qconnect(
                action.triggered, functools.partial(convert_and_insert, editor=webview.editor, source=ShowOptions.paste)
            )


def setup_editor_menus() -> None:
    from .config import config

    menus = Menus(config)
    gui_hooks.editor_did_init_buttons.append(menus.on_editor_did_init_buttons)
    gui_hooks.editor_did_init_shortcuts.append(menus.on_editor_did_init_shortcuts)
    gui_hooks.editor_will_show_context_menu.append(menus.on_editor_will_show_context_menu)


def init() -> None:
    setup_mainwindow_menu()
    setup_editor_menus()

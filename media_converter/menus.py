# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import os.path
from typing import Optional

from anki.utils import join_fields
from aqt import gui_hooks, mw
from aqt.editor import Editor, EditorWebView
from aqt.qt import *
from aqt.utils import tooltip

from .ajt_common.about_menu import menu_root_entry
from .ajt_common.media import find_all_media
from .common import insert_image_html, key_to_str
from .config import MediaConverterConfig, get_global_config
from .consts import ADDON_FULL_NAME, ADDON_NAME, ADDON_PATH
from .dialogs.main_settings_dialog import AnkiMainSettingsDialog
from .file_converters.file_converter import FFmpegNotFoundError
from .file_converters.image_converter import ffmpeg_not_found_dialog
from .file_converters.on_paste_converter import TEMP_IMAGE_FORMAT, OnPasteConverter
from .media_deduplication.anki_collection_op import run_media_deduplication
from .media_rename import MediaRenameDialog
from .utils.show_options import ShowOptions
from .utils.temp_file import TempFile


def setup_mainwindow_menu(config: MediaConverterConfig) -> None:
    """
    setup menu in anki
    """
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


def get_clipboard_mime_data(editor: Editor) -> QMimeData | None:
    clip = editor.mw.app.clipboard()
    if not clip:
        return None
    return clip.mimeData()


class EditorMenus:
    """Holds a reference to MediaRenameDialog to avoid spawning the same window multiple times."""

    _cfg: MediaConverterConfig
    _file_rename_dialog: Optional[MediaRenameDialog]

    def __init__(self, cfg: MediaConverterConfig):
        self._cfg = cfg
        self._file_rename_dialog = None

    def del_ref(self) -> None:
        self._file_rename_dialog = None

    def show_rename_dialog(self, editor: Editor) -> None:
        if self._file_rename_dialog:
            return
        elif editor.note and (filenames := find_all_media(join_fields(editor.note.fields))):
            d = self._file_rename_dialog = MediaRenameDialog(editor, editor.note, filenames)
            qconnect(d.finished, lambda result: self.del_ref())
            d.show()
        else:
            tooltip(
                "No files found on this card.",
                period=self._cfg.tooltip_duration_milliseconds,
                parent=editor.parentWindow,
            )

    def add_rename_files_button(self, buttons: list[str], editor: Editor) -> None:
        b = editor.addButton(
            icon=os.path.join(ADDON_PATH, "icons", "edit.svg"),
            cmd="ajt__rename_media_files",
            func=self.show_rename_dialog,
            tip="Rename media files referenced by note.",
        )
        buttons.append(b)

    def _convert_and_insert(self, editor: Editor, source: ShowOptions) -> None:
        mime: QMimeData | None = get_clipboard_mime_data(editor)
        conv = OnPasteConverter(editor, source, config=self._cfg)
        if not mime:
            conv.tooltip("Nothing to convert.")
            return
        with TempFile(suffix=f".{TEMP_IMAGE_FORMAT}") as tmp_file:
            if to_convert := conv.mime_to_image_file(mime, tmp_file.path()):
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
            else:
                conv.tooltip("Nothing to convert.")

    def add_paste_and_convert_button(self, buttons: list[str], editor: Editor) -> None:
        """
        Append a new editor button if it's enabled.
        """
        if self._cfg.show_editor_button:
            buttons.append(
                editor.addButton(
                    icon=os.path.join(ADDON_PATH, "icons", "webp.png"),
                    cmd=f"ajt__{ADDON_FULL_NAME.lower().replace(' ', '_')}_button",
                    func=functools.partial(self._convert_and_insert, source=ShowOptions.toolbar),
                    tip=self._action_tooltip(),
                    keys=self._cfg.shortcut or None,
                )
            )

    def _action_tooltip(self) -> str:
        return (
            f"{ADDON_FULL_NAME}: Paste"
            if not self._cfg.shortcut
            else f"{ADDON_FULL_NAME}: Paste ({key_to_str(self._cfg.shortcut)})"
        )

    def append_editor_shortcuts(self, cuts: list[tuple], editor: Editor) -> None:
        """
        Add keyboard shortcut if it is set and if editor button is disabled.
        If editor button is enabled, it has its own keyboard shortcut.
        """
        if not self._cfg.show_editor_button and self._cfg.shortcut:
            cuts.append((
                self._cfg.shortcut,
                functools.partial(self._convert_and_insert, editor=editor, source=ShowOptions.paste),
            ))

    def add_context_menu_entry(self, webview: EditorWebView, menu: QMenu) -> None:
        if self._cfg.show_context_menu_entry:
            action: QAction | None = menu.addAction(self._action_tooltip())
            if not action:
                return
            qconnect(
                action.triggered,
                functools.partial(self._convert_and_insert, editor=webview.editor, source=ShowOptions.paste),
            )


def setup_editor_menus(cfg: MediaConverterConfig) -> None:
    mw._ajt__media_converter_editor_menus = menus = EditorMenus(cfg)

    gui_hooks.editor_did_init_buttons.append(menus.add_rename_files_button)
    gui_hooks.editor_did_init_buttons.append(menus.add_paste_and_convert_button)
    gui_hooks.editor_did_init_shortcuts.append(menus.append_editor_shortcuts)
    gui_hooks.editor_will_show_context_menu.append(menus.add_context_menu_entry)


def init() -> None:
    assert mw, "Anki should be open."
    cfg = get_global_config()
    setup_mainwindow_menu(cfg)
    setup_editor_menus(cfg)

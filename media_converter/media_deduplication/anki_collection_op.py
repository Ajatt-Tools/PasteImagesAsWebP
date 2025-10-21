# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import pathlib

from aqt import mw, qconnect
from aqt.operations import CollectionOp
from aqt.utils import show_info

from ..dialogs.deduplicate_dialog import (
    DeduplicateMediaConfirmDialog,
    DeduplicateTableColumns,
)
from .deduplication import MediaDedup


def show_deduplication_confirm_dialog(files: dict[pathlib.Path, pathlib.Path]) -> DeduplicateMediaConfirmDialog:
    dialog = DeduplicateMediaConfirmDialog(column_names=DeduplicateTableColumns.column_names(), parent=mw)
    dialog.load_data([DeduplicateTableColumns(dup.name, orig.name) for dup, orig in files.items()])
    return dialog


def deduplicate_media_files(dedup: MediaDedup, files: dict[pathlib.Path, pathlib.Path]) -> None:
    CollectionOp(parent=mw, op=lambda col: dedup.deduplicate_notes_op(files)).success(
        lambda out: show_info(
            f'Deduplicated {len(files)} files. Don\'t forget to run "Tools" -> "Check Media".',
            parent=mw,
        ),
    ).run_in_background()


def run_media_deduplication() -> None:
    dedup = MediaDedup(col=mw.col)
    files = dedup.collect_files()
    if not files:
        show_info("No duplicate media files found.", parent=mw)
        return
    dialog = show_deduplication_confirm_dialog(files)
    qconnect(dialog.accepted, functools.partial(deduplicate_media_files, dedup, files))
    dialog.show()

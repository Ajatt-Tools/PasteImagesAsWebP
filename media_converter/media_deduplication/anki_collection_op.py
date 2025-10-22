# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import pathlib

from aqt import mw, qconnect
from aqt.operations import CollectionOp, QueryOp
from aqt.utils import show_info

from ..common import tooltip
from ..dialogs.deduplicate_dialog import (
    DeduplicateMediaConfirmDialog,
    DeduplicateTableColumns,
)
from .deduplication import MediaDedup


def show_deduplication_confirm_dialog(files: dict[pathlib.Path, pathlib.Path]) -> DeduplicateMediaConfirmDialog:
    dialog = DeduplicateMediaConfirmDialog(column_names=DeduplicateTableColumns.column_names(), parent=mw)
    dialog.load_data([DeduplicateTableColumns(dup.name, orig.name) for dup, orig in files.items()])
    return dialog


def deduplication_result_msg(n_files: int) -> str:
    return f'Deduplicated {n_files} files. Don\'t forget to run "Tools" -> "Check Media".'


def deduplicate_media_files(dedup: MediaDedup, files: dict[pathlib.Path, pathlib.Path]) -> None:
    CollectionOp(
        parent=mw,
        op=lambda col: dedup.deduplicate_notes_op(files),
    ).success(
        lambda out: show_info(
            deduplication_result_msg(len(files)),
            parent=mw,
        ),
    ).run_in_background()


def process_duplicates_search_results(dedup: MediaDedup, files: dict[pathlib.Path, pathlib.Path]) -> None:
    if not files:
        show_info("No duplicate media files found.", parent=mw)
        return
    dialog = show_deduplication_confirm_dialog(files)
    qconnect(dialog.accepted, functools.partial(deduplicate_media_files, dedup, files))
    qconnect(dialog.rejected, lambda: tooltip("Aborted.", parent=mw))
    dialog.show()


def run_media_deduplication() -> None:
    dedup = MediaDedup(col=mw.col)
    QueryOp(
        parent=mw,
        op=lambda collection: dedup.collect_files(),
        success=lambda result: process_duplicates_search_results(dedup, result),
    ).without_collection().with_progress("Searching for duplicate media files...").run_in_background()

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import functools
import typing
from collections.abc import Sequence

import anki.collection
from aqt import mw, qconnect
from aqt.operations import CollectionOp, QueryOp
from aqt.utils import show_info, tooltip

from ..config import MediaConverterConfig
from ..dialogs.deduplicate_dialog import (
    DeduplicateMediaConfirmDialog,
    DeduplicateTableColumns,
)
from .deduplication import DuplicatesGroup, MediaDedup


def show_deduplication_confirm_dialog(files: Sequence[DuplicatesGroup]) -> DeduplicateMediaConfirmDialog:
    dialog = DeduplicateMediaConfirmDialog(column_names=DeduplicateTableColumns.column_names(), parent=mw)
    dialog.load_data([
        DeduplicateTableColumns(duplicate_name=dup.name, original_name=group.original.name)
        for group in files
        for dup in group.copies
    ])
    return dialog


def deduplication_result_msg(n_files: int) -> str:
    return f'Deduplicated {n_files} files. Don\'t forget to run "Tools" -> "Check Media".'


class AnkiMediaDedup:
    _col: anki.collection.Collection
    _nproc: int
    _config: MediaConverterConfig

    def __init__(self, col: anki.collection.Collection, config: MediaConverterConfig) -> None:
        self._dedup = MediaDedup(col)
        self._config = config

    def collect_files(self) -> typing.Sequence[DuplicatesGroup]:
        return self._dedup.collect_files()

    def _deduplicate_media_files(self, files: Sequence[DuplicatesGroup], row_count: int) -> None:
        CollectionOp(
            parent=mw,
            op=lambda col: self._dedup.deduplicate_notes_op(files, row_count),
        ).success(
            lambda out: show_info(
                deduplication_result_msg(row_count),
                parent=mw,
            ),
        ).run_in_background()

    def process_duplicates_search_results(self, files: Sequence[DuplicatesGroup]) -> None:
        if not files:
            show_info("No duplicate media files found.", parent=mw)
            return
        dialog = show_deduplication_confirm_dialog(files)
        qconnect(dialog.accepted, functools.partial(self._deduplicate_media_files, files, dialog.row_count()))
        qconnect(
            dialog.rejected, lambda: tooltip("Aborted.", period=self._config.tooltip_duration_millisecond, parent=mw)
        )
        dialog.show()


def run_media_deduplication() -> None:
    from ..config import config

    dedup = AnkiMediaDedup(col=mw.col, config=config)
    QueryOp(
        parent=mw,
        op=lambda collection: dedup.collect_files(),
        success=lambda result: dedup.process_duplicates_search_results(result),
    ).without_collection().with_progress("Searching for duplicate media files...").run_in_background()

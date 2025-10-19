# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import collections
import os
import concurrent.futures
from collections.abc import Iterable, Sequence
from typing import Optional

from anki.collection import Collection
from anki.notes import Note, NoteId
from anki.utils import join_fields
from aqt import mw
from aqt.browser import Browser
from aqt.operations import CollectionOp, ResultWithChanges

from ..bulk_convert.convert_result import ConvertResult
from ..common import find_convertible_audio, find_convertible_images
from ..config import config
from ..dialogs.bulk_convert_result_dialog import BulkConvertResultDialog
from ..file_converters.common import LocalFile
from ..file_converters.internal_file_converter import InternalFileConverter


class ConvertTask:
    _browser: Browser
    _selected_fields: list[str]
    _result: ConvertResult
    _to_convert: dict[LocalFile, dict[NoteId, Note]]
    canceled: bool

    def __init__(self, browser: Browser, note_ids: Sequence[NoteId], selected_fields: list[str]):
        self._browser = browser
        self._selected_fields = selected_fields
        self._result = ConvertResult()
        self._to_convert = self._find_files_to_convert_and_notes(note_ids)
        self.canceled = False

    @property
    def size(self) -> int:
        return len(self._to_convert)

    def set_canceled(self) -> None:
        self.canceled = True

    def __call__(self):
        """
        Execute the conversion using ThreadPoolExecutor for parallelism while reporting progress.
        The conversion is performed in parallel; the order of completion is not guaranteed.
        If the task is canceled, all pending jobs are cancelled and no further
        conversions are started.  Running conversions are allowed to finish but
        their results are ignored.
        """
        if self._result.is_dirty():
            raise RuntimeError("Already converted.")
        files = list(self._to_convert.keys())
        max_workers = os.cpu_count() // 2 or 1

        def convert_file(file: LocalFile) -> tuple[LocalFile, Optional[str], Optional[Exception]]:
            """
            Convert a single file.  Returns a tuple of (file, new_filename, exception).
            If the task has been canceled, returns (file, None, None) immediately.
            """
            if self.canceled:
                return (file, None, None)
            try:
                converted_filename = self._convert_stored_file(file)
                return (file, converted_filename, None)
            except Exception as ex:
                return (file, None, ex)

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(convert_file, f): f for f in files}
            for future in concurrent.futures.as_completed(future_to_file):
                if self.canceled:
                    # Cancel all remaining futures that have not started yet
                    for f in future_to_file:
                        if not f.done():
                            f.cancel()
                    break
                file = future_to_file[future]
                try:
                    f, converted, exc = future.result()
                except Exception as ex:
                    # This should not happen because convert_file catches all exceptions
                    exc = ex
                    converted = None
                if exc:
                    self._result.add_failed(file, exception=exc)
                elif converted is not None:
                    self._result.add_converted(file, converted)
                completed += 1
                yield completed

    def update_notes(self):
        def show_report_message() -> int:
            dialog = BulkConvertResultDialog(self._browser)
            dialog.set_result(self._result)
            return dialog.exec()

        def on_finish() -> None:
            assert self._browser.editor
            show_report_message()
            self._browser.editor.loadNoteKeepingFocus()

        if self._result.is_dirty():
            if not self._result.converted:
                return show_report_message()
            CollectionOp(parent=self._browser, op=lambda col: self._update_notes_op(col)).success(
                lambda out: on_finish()
            ).run_in_background()

    def _first_referenced(self, file: LocalFile) -> Note:
        return next(note for note in self._to_convert[file].values())

    def _keys_to_update(self, note: Note) -> Iterable[str]:
        if not self._selected_fields:
            return note.keys()
        else:
            return set(note.keys()).intersection(self._selected_fields)

    def _find_files_to_convert_and_notes(self, note_ids: Sequence[NoteId]) -> dict[LocalFile, dict[NoteId, Note]]:
        """
        Maps each filename to a set of note ids that reference the filename.
        """
        assert mw
        to_convert: dict[LocalFile, dict[NoteId, Note]] = collections.defaultdict(dict)

        for note in map(mw.col.get_note, note_ids):
            note_content = join_fields([note[field] for field in self._keys_to_update(note)])
            if "<img" not in note_content and "[sound:" not in note_content:
                continue
            if config.enable_image_conversion:
                for filename in find_convertible_images(note_content, include_converted=config.bulk_reconvert):
                    to_convert[LocalFile.image(filename)][note.id] = note
            if config.enable_audio_conversion:
                # TODO config.bulk_reconvert
                for filename in find_convertible_audio(note_content, include_converted=False):
                    to_convert[LocalFile.audio(filename)][note.id] = note
        return to_convert

    def _convert_stored_file(self, file: LocalFile) -> str:
        """
        Convert a single file.  If the task has been canceled, the conversion
        is skipped and a dummy filename is returned.  This allows the worker
        threads to exit quickly without performing any work.
        """
        if self.canceled:
            # Return the original filename to avoid changing the note
            return file.file_name
        conv = InternalFileConverter(self._browser.editor, file, self._first_referenced(file))
        conv.convert_internal()
        return conv.new_filename

    def _update_notes_op(self, col: Collection) -> ResultWithChanges:
        pos = col.add_custom_undo_entry(f"Convert {len(self._result.converted)} images to WebP")
        to_update: dict[NoteId, Note] = {}

        for old_file, converted_filename in self._result.converted.items():
            for note in self._to_convert[old_file].values():
                for field_name in self._keys_to_update(note):
                    note[field_name] = note[field_name].replace(old_file.file_name, converted_filename)
                to_update[note.id] = note

        col.update_notes(list(to_update.values()))
        return col.merge_undo_entries(pos)

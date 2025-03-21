# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import collections
from collections.abc import Iterable, Sequence

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

    def __init__(self, browser: Browser, note_ids: Sequence[NoteId], selected_fields: list[str]):
        self._browser = browser
        self._selected_fields = selected_fields
        self._result = ConvertResult()
        self._to_convert = self._find_files_to_convert_and_notes(note_ids)

    @property
    def size(self) -> int:
        return len(self._to_convert)

    def __call__(self):
        if self._result.is_dirty():
            raise RuntimeError("Already converted.")
        for progress_idx, file in enumerate(self._to_convert):
            yield progress_idx
            try:
                converted_filename = self._convert_stored_file(file)
            except (OSError, RuntimeError, FileNotFoundError) as ex:
                self._result.add_failed(file, exception=ex)
            else:
                self._result.add_converted(file, converted_filename)

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

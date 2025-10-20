# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import hashlib
import os.path
import pathlib
import typing

import anki.errors
from anki.collection import Collection, OpChanges
from anki.notes import NoteId, Note
from aqt.operations import ResultWithChanges
from aqt.qt import *

from media_converter.dialogs.deduplicate_dialog import DeduplicateMediaConfirmDialog, DeduplicateTableColumns

HASH_FUNC = hashlib.sha512
CHUNK_SIZE: int = 8192


class DeduplicationError(RuntimeError):
    pass


class MediaDedupFileHash(typing.NamedTuple):
    hash: bytes
    file_size: int


def compute_file_hash(path: pathlib.Path) -> MediaDedupFileHash:
    # https://www.geeksforgeeks.org/python/python-program-to-find-hash-of-file/
    if not path.is_file():
        raise ValueError(f"{path} is not a file.")
    h = HASH_FUNC()
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):  # Read the file in chunks of 8192 bytes
            h.update(chunk)
    return MediaDedupFileHash(h.digest(), os.path.getsize(path))


class MediaDedup:
    _col: Collection

    def __init__(self, col: Collection) -> None:
        self._col = col

    def collect_files(self) -> dict[pathlib.Path, pathlib.Path]:
        """
        Returns a map duplicate_filename -> canonical_filename (first seen with same content).
        """
        hash_to_name: dict[MediaDedupFileHash, pathlib.Path] = {}
        duplicates: dict[pathlib.Path, pathlib.Path] = {}
        for entry in pathlib.Path(self._col.media.dir()).iterdir():
            if not entry.is_file() or entry.name.startswith("_"):
                # files starting with "_" are special
                continue
            try:
                file_hash = compute_file_hash(entry)
            except (OSError, IOError) as ex:
                print(f"error when computing hash: {ex}")
                continue
            if file_hash not in hash_to_name:
                hash_to_name[file_hash] = entry
                continue
            # already seen content -> mark this filename as duplicate
            duplicates[entry] = hash_to_name[file_hash]
        return duplicates

    def update_notes_op(self, files: dict[pathlib.Path, pathlib.Path]) -> ResultWithChanges:
        pos = self._col.add_custom_undo_entry(f"Replace media links to {len(files)} in notes")
        self.deduplicate(files)
        return self._col.merge_undo_entries(pos)

    def _deduplicate_note(self, note_id: NoteId, dup_name: str, orig_name: str) -> Note:
        note = self._col.get_note(note_id)
        for field_name in note.keys():
            note[field_name] = note[field_name].replace(f' src="{dup_name}"', f' src="{orig_name}"')
            note[field_name] = note[field_name].replace(f" src='{dup_name}'", f" src='{orig_name}'")
            note[field_name] = note[field_name].replace(f"[sound:{dup_name}]", f"[sound:{orig_name}]")
        return note

    def deduplicate(self, files: dict[pathlib.Path, pathlib.Path]) -> OpChanges:
        to_update: dict[NoteId, Note] = {}
        for dup, orig in files.items():
            search_string = self._col.build_search_string(dup.name)
            for note_id in self._col.find_notes(query=search_string):
                try:
                    to_update[note_id] = self._deduplicate_note(note_id, dup.name, orig.name)
                except anki.errors.NotFoundError:
                    print(f"note id={note_id} not found")
        return self._col.update_notes(list(to_update.values()))


def show_deduplication_confirm_dialog(files: dict[pathlib.Path, pathlib.Path]) -> DeduplicateMediaConfirmDialog:
    dialog = DeduplicateMediaConfirmDialog(column_names=DeduplicateTableColumns.column_names())
    dialog.load_data([DeduplicateTableColumns(dup.name, orig.name) for dup, orig in files.items()])
    dialog.show()
    return dialog

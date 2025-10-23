# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import collections
import concurrent.futures
import hashlib
import math
import multiprocessing
import os.path
import pathlib
import typing
from collections.abc import MutableSequence

import anki.collection
import anki.errors
from anki.notes import Note, NoteId
from aqt.operations import ResultWithChanges
from aqt.qt import *

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


class DuplicatesGroup(typing.NamedTuple):
    original: pathlib.Path
    copies: list[pathlib.Path]

    @classmethod
    def from_list(cls, files: collections.abc.Collection[pathlib.Path]) -> "DuplicatesGroup":
        assert len(files) > 1, "a group of duplicates should contain at least two files"
        files = sorted(files, key=lambda file: len(file.name))
        # Assign the shortest name as the original.
        return cls(original=files[0], copies=files[1:])


def deduplicate_media_in_note(note: Note, dup_name: str, orig_name: str) -> Note:
    for field_name in note.keys():
        note[field_name] = note[field_name].replace(f' src="{dup_name}"', f' src="{orig_name}"')
        note[field_name] = note[field_name].replace(f" src='{dup_name}'", f" src='{orig_name}'")
        note[field_name] = note[field_name].replace(f"[sound:{dup_name}]", f"[sound:{orig_name}]")
    return note


T = TypeVar("T")


def split_list(input_list: typing.Sequence[T], n_chunks: int) -> typing.Iterable[typing.Sequence[T]]:
    """Splits a list into N chunks."""
    chunk_size = math.ceil(len(input_list) / n_chunks)
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i : i + chunk_size]


def hash_files(files: typing.Sequence[pathlib.Path]) -> dict[MediaDedupFileHash, list[pathlib.Path]]:
    hash_to_names: dict[MediaDedupFileHash, list[pathlib.Path]] = collections.defaultdict(list)
    for entry in files:
        if not entry.is_file() or entry.name.startswith("_"):
            # files starting with "_" are special to Anki.
            continue
        try:
            file_hash = compute_file_hash(entry)
        except OSError as ex:
            print(f"error when computing hash: {ex}")
            continue
        hash_to_names[file_hash].append(entry)
    return hash_to_names


class MediaDedup:
    _col: anki.collection.Collection
    _nproc: int

    def __init__(self, col: anki.collection.Collection) -> None:
        self._col = col
        self._nproc = multiprocessing.cpu_count()

    def collect_files(self) -> typing.Sequence[DuplicatesGroup]:
        """
        Returns a list of groups.
        """
        result: dict[MediaDedupFileHash, MutableSequence[pathlib.Path]] = collections.defaultdict(list)

        # https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor-example
        # We can use a with statement to ensure threads are cleaned up promptly
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._nproc) as executor:
            # Start the load operations and mark each future with its URL
            futures = (
                executor.submit(hash_files, group)
                for group in split_list(list(pathlib.Path(self._col.media.dir()).iterdir()), n_chunks=self._nproc)
            )
            for future in concurrent.futures.as_completed(futures):
                try:
                    hash_to_names: dict[MediaDedupFileHash, list[pathlib.Path]] = future.result()
                except Exception as exc:
                    print(f"thread generated an exception: {exc}")
                    raise
                for hash_key, names in hash_to_names.items():
                    result[hash_key].extend(names)
        return [DuplicatesGroup.from_list(files) for files in result.values() if len(files) > 1]

    def deduplicate_notes_op(self, files: typing.Sequence[DuplicatesGroup], row_count: int) -> ResultWithChanges:
        pos = self._col.add_custom_undo_entry(f"Replace media links to {row_count} files in notes")
        self.deduplicate(files)
        return self._col.merge_undo_entries(pos)

    def _deduplicate_group(self, group: DuplicatesGroup, to_update: dict[NoteId, Note]) -> dict[NoteId, Note]:
        for dup in group.copies:
            for note_id in self._col.find_notes(query=self._col.build_search_string(dup.name)):
                try:
                    to_update.setdefault(note_id, self._col.get_note(note_id))
                except anki.errors.NotFoundError:
                    print(f"note id={note_id} not found")
                    continue
                deduplicate_media_in_note(to_update[note_id], dup.name, group.original.name)
        return to_update

    def deduplicate(self, files: typing.Sequence[DuplicatesGroup]) -> anki.collection.OpChanges:
        to_update: dict[NoteId, Note] = {}
        for group in files:
            self._deduplicate_group(group, to_update)
        return self._col.update_notes(list(to_update.values()))

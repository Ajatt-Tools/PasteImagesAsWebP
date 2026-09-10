# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pathlib
from collections.abc import Sequence
from unittest.mock import create_autospec, patch

import pytest
from anki.collection import Collection

from media_converter.config import MediaConverterConfig
from media_converter.media_deduplication.anki_collection_op import AnkiMediaDedup
from media_converter.media_deduplication.deduplication import (
    DuplicatesGroup,
    MediaDedup,
    compute_file_hash,
    do_replacements,
    hash_files,
    split_list,
)


@pytest.mark.parametrize(
    "content, old_name, new_name, expected",
    [
        ('<img src="old.png">', "old.png", "new.png", '<img src="new.png">'),
        ("<img src='old.png'>", "old.png", "new.png", "<img src='new.png'>"),
        ('<a href="old.png">link</a>', "old.png", "new.png", '<a href="new.png">link</a>'),
        ("<a href='old.png'>link</a>", "old.png", "new.png", "<a href='new.png'>link</a>"),
        ("[sound:old.mp3]", "old.mp3", "new.ogg", "[sound:new.ogg]"),
        ('url("old.png")', "old.png", "new.png", 'url("new.png")'),
        ("url('old.png')", "old.png", "new.png", "url('new.png')"),
        ("url(old.png)", "old.png", "new.png", "url(new.png)"),
        ("url(&quot;old.png&quot;)", "old.png", "new.png", "url(&quot;new.png&quot;)"),
        ("url(&#39;old.png&#39;)", "old.png", "new.png", "url(&#39;new.png&#39;)"),
        ('<img src="other.png">', "old.png", "new.png", '<img src="other.png">'),
        ('<img src="old.png">[sound:old.png]', "old.png", "new.png", '<img src="new.png">[sound:new.png]'),
        ('<img src="ba.png">', "a.png", "new.png", '<img src="ba.png">'),
        (">old.png<", "old.png", "new.png", ">new.png<"),
        ("some old.png text", "old.png", "new.png", "some new.png text"),
    ],
    ids=[
        "src_double_quotes",
        "src_single_quotes",
        "href_double_quotes",
        "href_single_quotes",
        "sound_tag",
        "css_url_double_quotes",
        "css_url_single_quotes",
        "css_url_no_quotes",
        "css_url_html_entities_double",
        "css_url_html_entities_single",
        "no_match_unchanged",
        "multiple_occurrences",
        "substring_not_replaced",
        "plain_text_gt_lt",
        "space_surrounded",
    ],
)
def test_do_replacements(content: str, old_name: str, new_name: str, expected: str) -> None:
    assert do_replacements(content, old_name, new_name) == expected


class TestDeduplicationSequenceAnnotations:
    """Keep sequence-based APIs usable with mutable and immutable inputs under beartype."""

    @pytest.mark.parametrize(
        ("values", "chunk_count", "expected"),
        [
            ([1, 2, 3, 4], 2, [[1, 2], [3, 4]]),
            ((1, 2, 3, 4), 2, [(1, 2), (3, 4)]),
            ([1, 2, 3], 2, [[1, 2], [3]]),
            ((1, 2), 4, [(1,), (2,)]),
        ],
    )
    def test_split_list(self, values: Sequence[int], chunk_count: int, expected: Sequence[Sequence[int]]) -> None:
        """Chunking preserves each input sequence's slice behavior."""
        assert list(split_list(values, chunk_count)) == expected

    @pytest.mark.parametrize("use_tuple", [False, True])
    def test_hash_files(self, tmp_path: pathlib.Path, use_tuple: bool) -> None:
        """Hashing accepts either sequence representation and groups identical contents."""
        original = tmp_path / "original.png"
        copy = tmp_path / "copy.png"
        original.write_bytes(b"matching contents")
        copy.write_bytes(original.read_bytes())
        paths: Sequence[pathlib.Path] = [original, copy]
        if use_tuple:
            paths = tuple(paths)
        assert hash_files(paths) == {compute_file_hash(original): [original, copy]}

    @pytest.mark.parametrize("use_tuple", [False, True])
    def test_collection_wrapper(self, no_anki_config: MediaConverterConfig, use_tuple: bool) -> None:
        """The Anki wrapper returns either valid sequence form without coercing the result."""
        groups: Sequence[DuplicatesGroup] = [DuplicatesGroup(pathlib.Path("a.png"), [pathlib.Path("copy.png")])]
        if use_tuple:
            groups = tuple(groups)
        wrapper = AnkiMediaDedup(create_autospec(Collection, instance=True), no_anki_config)
        with patch.object(MediaDedup, "collect_files", return_value=groups):
            assert wrapper.collect_files() is groups

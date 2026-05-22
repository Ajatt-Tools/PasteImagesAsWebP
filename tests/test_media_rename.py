# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

from media_converter.media_rename import (
    FileNameEdit,
    MediaRenameDialog,
    RenameTask,
    format_report_message,
)


class TestFileNameEdit:
    """Tests for FileNameEdit validation and text processing."""

    @pytest.mark.parametrize(
        "filename",
        [
            "image.png",
            "my-file_01.webp",
            "日本語.mp3",
            "photo.avif",
            "a.b",
            "file with spaces.ogg",
        ],
    )
    def test_valid_filenames(self, filename: str) -> None:
        edit = FileNameEdit(text=filename)
        assert edit.valid, f"Expected '{filename}' to be valid"

    @pytest.mark.parametrize(
        "filename",
        [
            "file[1].png",
            "file].png",
            "file<.png",
            "file>.png",
            "file:.png",
            'file".png',
            "file/.png",
            "file|.png",
            "file?.png",
            "file*.png",
            "file\\.png",
            "noext",
            "file.",
            "file.abcdef",
            "あ" * 40 + ".png",  # 124 bytes UTF-8 > 119
        ],
        ids=[
            "bracket_open",
            "bracket_close",
            "less_than",
            "greater_than",
            "colon",
            "double_quote",
            "slash",
            "pipe",
            "question_mark",
            "asterisk",
            "backslash",
            "no_extension",
            "dot_only",
            "extension_too_long",
            "too_long_utf8",
        ],
    )
    def test_invalid_filenames(self, filename: str) -> None:
        edit = FileNameEdit(text=filename)
        assert not edit.valid, f"Expected '{filename}' to be invalid"

    @pytest.mark.parametrize(
        "input_text, expected",
        [
            ("  _-image.png-_ ", "image.png"),
            ("my_file-name.png", "my_file-name.png"),
        ],
        ids=["strips_leading_trailing", "preserves_middle"],
    )
    def test_text_strip(self, input_text: str, expected: str) -> None:
        edit = FileNameEdit(text=input_text)
        assert edit.text() == expected


class TestMediaRenameDialog:
    """Tests for MediaRenameDialog.to_rename() and can_rename_all_files()."""

    def test_to_rename_yields_changed(self) -> None:
        dialog = MediaRenameDialog(["old.png"])
        dialog.edits["old.png"].setText("new.png")
        results = list(dialog.to_rename())
        assert results == [RenameTask("old.png", "new.png")]

    def test_to_rename_skips_unchanged(self) -> None:
        dialog = MediaRenameDialog(["same.png"])
        results = list(dialog.to_rename())
        assert results == []

    def test_to_rename_skips_invalid(self) -> None:
        dialog = MediaRenameDialog(["old.png"])
        dialog.edits["old.png"].setText("invalid[name")
        results = list(dialog.to_rename())
        assert results == []

    def test_to_rename_multiple_files(self) -> None:
        dialog = MediaRenameDialog(["a.png", "b.mp3", "c.webp"])
        dialog.edits["a.png"].setText("renamed_a.png")
        # b.mp3 unchanged
        dialog.edits["c.webp"].setText("renamed_c.webp")
        results = list(dialog.to_rename())
        assert RenameTask("a.png", "renamed_a.png") in results
        assert RenameTask("c.webp", "renamed_c.webp") in results
        assert len(results) == 2

    @pytest.mark.parametrize(
        "text_to_set, expected",
        [
            ("renamed.png", True),
            ("bad[name", False),
        ],
        ids=["all_valid", "one_invalid"],
    )
    def test_can_rename_all_files(self, text_to_set: str, expected: bool) -> None:
        dialog = MediaRenameDialog(["a.png", "b.mp3"])
        dialog.edits["a.png"].setText(text_to_set)
        assert dialog.can_rename_all_files() == expected

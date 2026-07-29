# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pathlib

import pytest
from aqt.qt import QImage, QMimeData, Qt, QUrl

from media_converter.utils import mime_helper
from media_converter.utils.mime_helper import (
    has_local_files,
    image_candidates,
    image_from_file,
)


def write_valid_png(path: pathlib.Path) -> None:
    """Write a tiny valid PNG via Qt itself."""
    image = QImage(2, 2, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.red)
    assert image.save(str(path))


class TestHasLocalFiles:
    """Tests for has_local_files()."""

    @pytest.mark.parametrize(
        "urls, expected",
        [
            ([QUrl.fromLocalFile("/tmp/a.png")], True),
            ([QUrl("https://example.com/a.png")], False),
            ([QUrl.fromLocalFile("/tmp/a.png"), QUrl("https://example.com/b.png")], True),
            ([], False),
        ],
        ids=["local_file", "remote_only", "mixed", "empty"],
    )
    def test_urls(self, urls: list[QUrl], expected: bool) -> None:
        mime = QMimeData()
        mime.setUrls(urls)
        assert has_local_files(mime) == expected


class TestImageCandidates:
    """Tests for the macOS icns gating in image_candidates()."""

    @pytest.mark.parametrize(
        "is_mac, with_local_file, expect_file_image",
        [
            # Finder copy on macOS: imageData() (icns thumbnail) is skipped, file is read.
            (True, True, True),
            # Preview copy on macOS: no local file, imageData() is yielded (empty here).
            (True, False, False),
            # Other platforms: imageData() is yielded first even with a local file present.
            (False, True, False),
        ],
        ids=["mac_finder_skips_image_data", "mac_no_file_keeps_image_data", "other_os_keeps_image_data"],
    )
    def test_image_data_gating(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: pathlib.Path,
        is_mac: bool,
        with_local_file: bool,
        expect_file_image: bool,
    ) -> None:
        monkeypatch.setattr(mime_helper, "IS_MAC", is_mac)
        mime = QMimeData()
        if with_local_file:
            png_path = tmp_path / "real.png"
            write_valid_png(png_path)
            mime.setUrls([QUrl.fromLocalFile(str(png_path))])
        first = next(image_candidates(mime))
        # When imageData() is skipped, the first candidate is the image read from the file.
        # When imageData() is yielded, it is None because this QMimeData carries no image payload.
        if expect_file_image:
            assert isinstance(first, QImage)
            assert not first.isNull()
        else:
            assert not isinstance(first, QImage) or first.isNull()


class TestImageFromFile:
    """Tests for image_from_file()."""

    @pytest.mark.parametrize(
        "content",
        [None, b"this is not an image"],
        ids=["missing_file", "garbage_bytes"],
    )
    def test_unusable_file_yields_no_image(self, tmp_path: pathlib.Path, content: bytes | None) -> None:
        path = tmp_path / "image.png"
        if content is not None:
            path.write_bytes(content)
        result = image_from_file(str(path))
        # Missing file -> None; undecodable bytes -> null QImage. Either way, no usable image.
        assert result is None or result.isNull()

    def test_valid_png(self, tmp_path: pathlib.Path) -> None:
        path = tmp_path / "valid.png"
        write_valid_png(path)
        result = image_from_file(str(path))
        assert result is not None
        assert not result.isNull()

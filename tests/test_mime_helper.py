# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pathlib
from unittest.mock import Mock

import pytest
from aqt.qt import QImage, QMimeData, Qt, QUrl
from requests.exceptions import InvalidSchema, Timeout

from media_converter.utils import mime_helper
from media_converter.utils.mime_helper import (
    data_from_html,
    has_local_files,
    image_candidates,
    image_from_file,
    image_from_url,
    iter_files,
    iter_urls,
    urls_from_html,
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


class TestUrlsFromHtml:
    """Tests for urls_from_html()."""

    @pytest.mark.parametrize(
        "html, expected",
        [
            ('<img src="http://example.com/a.png">', ["http://example.com/a.png"]),
            (
                '<img src="https://example.com/a.webp"><img src="http://example.com/b.jpg">',
                ["https://example.com/a.webp", "http://example.com/b.jpg"],
            ),
            ('<img src="file:///home/user/a.png">', []),
            ("plain text without images", []),
        ],
        ids=["single_url", "two_urls", "local_url_ignored", "no_urls"],
    )
    def test_extraction(self, html: str, expected: list[str]) -> None:
        assert urls_from_html(html) == expected


class TestDataFromHtml:
    """Tests for data_from_html()."""

    @pytest.mark.parametrize(
        "html, expected_data",
        [
            ('<img src="data:image/png;base64,aGVsbG8=">', [b"hello"]),
            ('<img src="data:image/png;base64,YQ=="><img src="data:image/png;base64,Yg==">', [b"a", b"b"]),
            ('<img src="http://example.com/a.png">', []),
        ],
        ids=["single_payload", "two_payloads", "no_payloads"],
    )
    def test_extraction(self, html: str, expected_data: list[bytes]) -> None:
        assert [bytes(data) for data in data_from_html(html)] == expected_data


class TestIterUrlsAndFiles:
    """Tests for iter_urls() and iter_files()."""

    def test_mixed_urls_are_split(self) -> None:
        mime = QMimeData()
        mime.setUrls([
            QUrl.fromLocalFile("/tmp/local.png"),
            QUrl("https://example.com/remote.png"),
        ])
        assert list(iter_files(mime)) == ["/tmp/local.png"]
        assert list(iter_urls(mime)) == ["https://example.com/remote.png"]

    def test_empty_mime_yields_nothing(self) -> None:
        mime = QMimeData()
        assert list(iter_files(mime)) == []
        assert list(iter_urls(mime)) == []


class TestImageFromUrl:
    """Tests for image_from_url() error paths."""

    @pytest.mark.parametrize(
        "exception",
        [Timeout("timed out"), InvalidSchema("bad scheme"), OSError("os error")],
        ids=["timeout", "invalid_schema", "os_error"],
    )
    def test_request_errors_yield_none(self, monkeypatch: pytest.MonkeyPatch, exception: Exception) -> None:
        monkeypatch.setattr(mime_helper.requests, "get", Mock(side_effect=exception))
        assert image_from_url("https://example.com/a.png") is None

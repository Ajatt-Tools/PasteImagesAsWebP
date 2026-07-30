# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
from collections.abc import Iterable

import requests
from aqt.qt import *
from requests.exceptions import InvalidSchema, Timeout

from ..consts import IS_MAC, REQUEST_HEADERS, REQUEST_TIMEOUTS

REMOTE_IMAGE_URL_RE = re.compile(r'(?<= src=")(?P<url>http[^"]+)(?=")')
BASE64_IMAGE_DATA_RE = re.compile(r'(?<=;base64,)(?P<data>[^"]+)(?=")')


def urls_from_html(html: str) -> list[str]:
    """Return remote image URLs embedded in HTML source attributes."""
    return [match.group("url") for match in REMOTE_IMAGE_URL_RE.finditer(html)]


def data_from_html(html: str) -> list[QByteArray]:
    """Return base64 image payloads embedded in HTML source attributes."""
    return [QByteArray.fromBase64(match.group("data").encode("ascii")) for match in BASE64_IMAGE_DATA_RE.finditer(html)]


def iter_urls(mime: QMimeData) -> Iterable[str]:
    """Yield remote URLs carried by the MIME data."""
    return (url.toString() for url in mime.urls() if not url.isLocalFile())


def iter_files(mime: QMimeData) -> Iterable[str]:
    """Yield local file paths carried by the MIME data."""
    return (url.toLocalFile() for url in mime.urls() if url.isLocalFile())


def image_from_url(src_url: str) -> QImage | None:
    """Download a remote image URL and return it as a QImage when possible."""
    image = QImage()
    try:
        with requests.get(src_url, timeout=REQUEST_TIMEOUTS, headers=REQUEST_HEADERS) as r:
            image.loadFromData(r.content)
    except (Timeout, InvalidSchema, OSError):
        return None
    return image


def image_from_file(filepath: str) -> QImage | None:
    """Read a local image file and return it as a QImage when possible."""
    try:
        with open(filepath, "rb") as f:
            return QImage.fromData(f.read())
    except OSError:
        # The file may have vanished between copy and paste, or be unreadable.
        # Return None so the caller can try the next candidate instead of crashing.
        return None


def has_local_files(mime: QMimeData) -> bool:
    """Return True if the clipboard contains at least one local file URL."""
    return any(url.isLocalFile() for url in mime.urls())


def image_candidates(mime: QMimeData) -> Iterable[QImage | None]:
    """Yield image candidates from direct image data, HTML, files, and URLs."""
    # On macOS, copying a file in Finder puts the file's .icns thumbnail on the clipboard.
    # Qt exposes it as imageData() ('application/x-qt-image') and does not reveal the raw 'public.icns' UTI,
    # so the thumbnail is indistinguishable from a genuine image by format alone.
    # The reliable signature of a Finder copy is a local file URL alongside image data.
    # Skip imageData(), but only on macOS, so genuine image payloads keep working everywhere else.
    if not (IS_MAC and has_local_files(mime)):
        yield mime.imageData()
    for data in data_from_html(mime.html()):
        yield QImage.fromData(data)
    for file in iter_files(mime):
        yield image_from_file(file)
    for url in iter_urls(mime):
        yield image_from_url(url)
    for url in urls_from_html(mime.html()):
        yield image_from_url(url)

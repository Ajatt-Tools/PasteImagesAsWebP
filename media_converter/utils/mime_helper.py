# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
from typing import Optional, Iterable

import requests
from aqt.qt import *
from requests.exceptions import Timeout, InvalidSchema

from ..consts import REQUEST_TIMEOUTS, REQUEST_HEADERS


def urls_from_html(html: str) -> list:
    return re.findall('(?<= src=")http[^"]+(?=")', html)


def data_from_html(html: str) -> list[QByteArray]:
    return [QByteArray.fromBase64(data.encode('ascii')) for data in re.findall('(?<=;base64,)[^"]+(?=")', html)]


def iter_urls(mime: QMimeData) -> Iterable[str]:
    return (url.toString() for url in mime.urls() if not url.isLocalFile())


def iter_files(mime: QMimeData) -> Iterable[str]:
    return (url.toLocalFile() for url in mime.urls() if url.isLocalFile())


def image_from_url(src_url: str) -> Optional[QImage]:
    image = QImage()
    try:
        with requests.get(src_url, timeout=REQUEST_TIMEOUTS, headers=REQUEST_HEADERS) as r:
            image.loadFromData(r.content)
    except (Timeout, InvalidSchema, OSError):
        return None
    return image


def image_from_file(filepath: str):
    with open(filepath, 'rb') as f:
        return QImage.fromData(f.read())


def image_candidates(mime: QMimeData) -> Iterable[Optional[QImage]]:
    yield mime.imageData()
    for data in data_from_html(mime.html()):
        yield QImage.fromData(data)
    for file in iter_files(mime):
        yield image_from_file(file)
    for url in iter_urls(mime):
        yield image_from_url(url)
    for url in urls_from_html(mime.html()):
        yield image_from_url(url)

# Paste Images As WebP add-on for Anki 2.1
# Copyright (C) 2021  Ren Tatsumoto. <tatsu at autistici.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Any modifications to this file must keep this entire header intact.

import re
from typing import Optional, Iterable, List, Tuple

import requests
from aqt.qt import *
from requests.exceptions import Timeout, InvalidSchema

from ..consts import REQUEST_TIMEOUTS, REQUEST_HEADERS


def urls_from_html(html: str) -> list:
    return re.findall('(?<= src=")http[^"]+(?=")', html)


def data_from_html(html: str) -> List[QByteArray]:
    return [QByteArray.fromBase64(data.encode('ascii')) for data in re.findall('(?<=;base64,)[^"]+(?=")', html)]


def urls(mime: QMimeData) -> Iterable[str]:
    return (url.toString() for url in mime.urls() if not url.isLocalFile())


def files(mime: QMimeData) -> Iterable[str]:
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
    for file in files(mime):
        yield image_from_file(file)
    for url in urls(mime):
        yield image_from_url(url)
    for url in urls_from_html(mime.html()):
        yield image_from_url(url)

# -*- coding: utf-8 -*-

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
from typing import Optional, Iterable, List

import requests
from aqt.qt import *
from requests.exceptions import Timeout

from ..consts import REQUEST_TIMEOUTS, REQUEST_HEADERS


def urls_from_html(html: str) -> list:
    return re.findall('(?<= src=")http[^"]+(?=")', html)


def data_from_html(html: str) -> List[QByteArray]:
    return [QByteArray.fromBase64(data.encode('ascii')) for data in re.findall('(?<=;base64,)[^"]+(?=")', html)]


def urls(mime: QMimeData):
    return (url.toString() for url in mime.urls())


def image_from_url(src_url) -> Optional[QImage]:
    image = QImage()
    try:
        file_contents = requests.get(src_url, timeout=REQUEST_TIMEOUTS, headers=REQUEST_HEADERS).content
        image.loadFromData(file_contents)
    except Timeout:
        return None
    return image


def image_candidates(mime: QMimeData) -> Iterable[Optional[QImage]]:
    yield mime.imageData()
    for data in data_from_html(mime.html()):
        yield QImage.fromData(data)
    for url in urls(mime):
        yield image_from_url(url)
    for url in urls_from_html(mime.html()):
        yield image_from_url(url)


def save_image(tmp_path: str, mime: QMimeData) -> bool:
    for image in image_candidates(mime):
        if image and image.save(tmp_path, 'png') is True:
            break
    else:
        return False

    return True

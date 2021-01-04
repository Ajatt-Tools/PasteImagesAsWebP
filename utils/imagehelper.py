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
import urllib
from typing import Optional, Iterable
from urllib.error import URLError

from aqt.qt import *


def urls_from_html_data(html) -> list:
    return re.findall('(?<= src=")http[^"]+(?=")', html)


def urls(mime: QMimeData):
    return (url.toString() for url in mime.urls())


def image_from_url(src_url) -> Optional[QImage]:
    image = QImage()
    try:
        req = urllib.request.Request(src_url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
        file_contents = urllib.request.urlopen(req).read()
        image.loadFromData(file_contents)
    except (ValueError, URLError):
        return None
    return image


def image_candidates(mime: QMimeData) -> Iterable[Optional[QImage]]:
    yield mime.imageData()
    for url in urls(mime):
        yield image_from_url(url)
    for url in urls_from_html_data(mime.html()):
        yield image_from_url(url)
    # yield image_from_url(mime.text())


def save_image(tmp_path: str, mime: QMimeData) -> bool:
    for image in image_candidates(mime):
        if image and image.save(tmp_path, 'png') is True:
            break
    else:
        return False

    return True

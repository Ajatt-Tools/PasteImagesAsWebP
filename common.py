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
from typing import Iterable, Optional
from typing import NamedTuple

from aqt.editor import Editor
from aqt.qt import *

from .config import config

RE_IMAGE_HTML_TAG = re.compile(r'<img[^<>]*src="([^"]+)"[^<>]*>', flags=re.IGNORECASE)


class ImageDimensions(NamedTuple):
    width: int
    height: int


def find_convertible_images(html: str, include_converted: bool = False) -> Iterable[str]:
    if not (html and '<img' in html):
        return
    filename: str
    for filename in re.findall(RE_IMAGE_HTML_TAG, html):
        if include_converted or not filename.endswith(config.image_extension):
            yield filename


def tooltip(msg: str, parent: Optional[QWidget] = None) -> None:
    from aqt.utils import tooltip as _tooltip

    return _tooltip(
        msg=msg,
        period=int(config.get('tooltip_duration_seconds', 5)) * 1000,
        parent=parent
    )


def filesize_kib(filepath: str) -> float:
    return os.stat(filepath).st_size / 1024.0


def image_html(image_filename: str) -> str:
    image_format = config.get('image_format')
    return f'<img alt="{image_format} image" src="{image_filename}">'


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=image_html(image_filename), internal=True)


def has_local_file(mime: QMimeData) -> bool:
    for url in mime.urls():
        if url.isLocalFile():
            return True
    return False


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.SequenceFormat.NativeText)

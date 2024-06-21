# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
from collections.abc import Iterable
from typing import NamedTuple, Optional

from aqt.editor import Editor
from aqt.qt import *

from .config import config

RE_IMAGE_HTML_TAG = re.compile(r'<img[^<>]*src="([^"]+)"[^<>]*>', flags=re.IGNORECASE)


class ImageDimensions(NamedTuple):
    width: int
    height: int


def find_convertible_images(html: str, include_converted: bool = False) -> Iterable[str]:
    if not (html and "<img" in html):
        return
    filename: str
    for filename in re.findall(RE_IMAGE_HTML_TAG, html):
        if include_converted or not filename.endswith(config.image_extension):
            yield filename


def tooltip(msg: str, parent: Optional[QWidget] = None) -> None:
    from aqt.utils import tooltip as _tooltip

    return _tooltip(msg=msg, period=int(config.get("tooltip_duration_seconds", 5)) * 1000, parent=parent)


def filesize_kib(filepath: str) -> float:
    return os.stat(filepath).st_size / 1024.0


def image_html(image_filename: str) -> str:
    return f'<img alt="{config.image_format.name} image" src="{image_filename}">'


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=image_html(image_filename), internal=True)


def has_local_file(mime: QMimeData) -> bool:
    for url in mime.urls():
        if url.isLocalFile():
            return True
    return False


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.SequenceFormat.NativeText)

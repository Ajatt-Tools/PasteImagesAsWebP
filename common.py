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
from typing import Iterable
from typing import NamedTuple

from aqt.editor import Editor
from aqt.qt import *

from .config import config

try:
    from anki.notes import NoteId
except ImportError:
    from typing import NewType

    NoteId = NewType("NoteId", int)

try:
    from anki.utils import join_fields
except ImportError:
    from anki.utils import joinFields as join_fields  # type: ignore

RE_IMAGE_HTML_TAG = re.compile(r'<img[^<>]*src="([^"]+)"[^<>]*>', flags=re.IGNORECASE)


class ImageDimensions(NamedTuple):
    width: int
    height: int


def find_convertible_images(html: str, include_webp: bool = False) -> Iterable[str]:
    for filename in re.findall(RE_IMAGE_HTML_TAG, html):
        filename: str
        if include_webp or not filename.endswith('.webp'):
            yield filename


def tooltip(msg: str) -> None:
    from aqt.utils import tooltip as _tooltip

    return _tooltip(
        msg=msg,
        period=int(config.get('tooltip_duration_seconds', 5)) * 1000
    )


def filesize_kib(filepath: str) -> float:
    return os.stat(filepath).st_size / 1024.0


def result_tooltip(filepath: str) -> None:
    tooltip(f"<strong>{os.path.basename(filepath)}</strong> added.<br>File size: {filesize_kib(filepath):.3f} KiB.")


def image_html(image_filename: str) -> str:
    return f'<img alt="webp image" src="{image_filename}">'


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=image_html(image_filename), internal=True)


def has_local_file(mime: QMimeData) -> bool:
    for url in mime.urls():
        if url.isLocalFile():
            return True
    return False


def custom_decorate(old: Callable, new: Callable):
    """Avoids crash by discarding args[1](=False) when called from context menu."""

    # https://forums.ankiweb.net/t/investigating-an-ambigous-add-on-error/12846
    def wrapper(*args):
        return new(args[0], _old=old)

    return wrapper


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.SequenceFormat.NativeText)

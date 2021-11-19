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

from aqt.editor import Editor
from aqt.qt import *
from aqt.utils import tooltip as __tooltip

from .config import config
from .utils.gui import ShowOptions
from .utils.webp import ImageConverter

try:
    from anki.notes import NoteId
except ImportError:
    from typing import NewType

    NoteId = NewType("NoteId", int)


def tooltip(msg: str) -> None:
    return __tooltip(
        msg=msg,
        period=int(config.get('tooltip_duration_seconds', 5)) * 1000
    )


def tooltip_filesize(filepath: os.PathLike) -> None:
    filesize_kib = str(os.stat(filepath).st_size / 1024)
    tooltip(f"Image added. File size: {filesize_kib[:filesize_kib.find('.') + 3]} KiB.")


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=f'<img src="{image_filename}">', internal=True)


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
    return QKeySequence(shortcut).toString(QKeySequence.NativeText)


def insert_webp(editor: Editor):
    mime: QMimeData = editor.mw.app.clipboard().mimeData()
    w = ImageConverter(editor, ShowOptions.menus)
    try:
        w.convert(mime)
        insert_image_html(editor, w.filename)
        tooltip_filesize(w.filepath)
    except Exception as ex:
        tooltip(str(ex))

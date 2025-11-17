# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re

from aqt.editor import Editor
from aqt.qt import *

from .file_converters.common import get_file_extension

RE_IMAGE_HTML_TAG = re.compile(r'<img[^<>]*src="(?P<name>[^"]+)"[^<>]*>', flags=re.IGNORECASE)
RE_AUDIO_HTML_TAG = re.compile(r"\[sound:(?P<name>[^]]+)]", flags=re.IGNORECASE)


def filesize_kib(filepath: str) -> float:
    return os.stat(filepath).st_size / 1024.0


def image_html(image_filename: str) -> str:
    return f'<img alt="{get_file_extension(image_filename).lstrip('.')} image" src="{image_filename}">'


def insert_image_html(editor: Editor, image_filename: str):
    editor.doPaste(html=image_html(image_filename), internal=True)


def has_local_file(mime: QMimeData) -> bool:
    for url in mime.urls():
        if url.isLocalFile():
            return True
    return False


def key_to_str(shortcut: str) -> str:
    return QKeySequence(shortcut).toString(QKeySequence.SequenceFormat.NativeText)

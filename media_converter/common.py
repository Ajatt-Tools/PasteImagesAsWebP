# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re
from collections.abc import Iterable
from typing import Optional

from aqt.editor import Editor
from aqt.qt import *
from .config import config
from .dialogs.paste_image_dialog import AnkiPasteImageDialog
from .utils.show_options import ImageDimensions, ShowOptions

RE_IMAGE_HTML_TAG = re.compile(r'<img[^<>]*src="([^"]+)"[^<>]*>', flags=re.IGNORECASE)
RE_AUDIO_HTML_TAG = re.compile(r"\[sound:([^\]]+)\]", flags=re.IGNORECASE)


def get_file_extension(file_path: str) -> str:
    return os.path.splitext(file_path)[1].lower()


def is_excluded_image_extension(filename: str, include_converted: bool = False) -> bool:
    """
    Return true if the image file with this filename should not be converted.

    :param filename: Name of the file.
    :param include_converted: Allow reconversion. The target extension (webp, avif) will not be excluded.
    """

    return get_file_extension(filename) in config.get_excluded_image_extensions(include_converted)


def is_excluded_audio_extension(filename: str, include_converted: bool = False) -> bool:
    """
    Return true if the audio file with this filename should not be converted.

    :param filename: Name of the file.
    :param include_converted: Allow reconversion. The target extension (webp, avif) will not be excluded.
    """

    return get_file_extension(filename) in config.get_excluded_audio_extensions(include_converted)


def find_convertible_images(html: str, include_converted: bool = False) -> Iterable[str]:
    """
    Find image files referenced by a note.
    :param html: Note content (joined fields).
    :param include_converted: Reconvert files even if they already have been converted to the target format. E.g. to reduce size.
    :return: Filenames
    """
    if "<img" not in html:
        return
    filename: str
    for filename in re.findall(RE_IMAGE_HTML_TAG, html):
        # Check if the filename ends with any of the excluded extensions
        if not is_excluded_image_extension(filename, include_converted):
            yield filename


def find_convertible_audio(html: str, include_converted: bool = False) -> Iterable[str]:
    """
    Find audio files referenced by a note.
    :param html: Note content (joined fields).
    :param include_converted: Reconvert files even if they already have been converted to the target format. E.g. to reduce size.
    :return: Filenames
    """
    if "[sound:" not in html:
        return
    filename: str
    for filename in re.findall(RE_AUDIO_HTML_TAG, html):
        # Check if the filename ends with any of the excluded extensions
        if not is_excluded_audio_extension(filename, include_converted):
            yield filename


def tooltip(msg: str, parent: Optional[QWidget] = None) -> None:
    from aqt.utils import tooltip as _tooltip


    return _tooltip(msg=msg, period=config.tooltip_duration_seconds * 1000, parent=parent)


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


def maybe_show_settings(dimensions: ImageDimensions, parent: Optional[QWidget], action: ShowOptions) -> int:
    if config.should_show_settings(action):
        dlg = AnkiPasteImageDialog(config=config, dimensions=dimensions, parent=parent)
        return dlg.exec()
    return QDialog.DialogCode.Accepted

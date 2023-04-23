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

import aqt.editor
from aqt import gui_hooks
from aqt.utils import KeyboardModifiersPressed

from .common import *
from .config import config
from .webp import ShowOptions, ImageConverter, CanceledPaste, InvalidInput


def should_paste_raw():
    return KeyboardModifiersPressed().shift


def convert_mime(mime: QMimeData, editor: Editor, action: ShowOptions):
    w = ImageConverter(editor, action)
    try:
        w.convert(mime)
    except InvalidInput:
        pass
    except CanceledPaste as ex:
        tooltip(str(ex))
    except RuntimeError as ex:
        tooltip(str(ex))
    except FileNotFoundError:
        tooltip("File not found.")
    else:
        mime = QMimeData()
        mime.setHtml(f'<img webp_converted="true" src="{w.filename}">')
        result_tooltip(w.filepath)

    return mime



def on_process_mime(
        mime: QMimeData,
        editor_web_view: aqt.editor.EditorWebView,
        internal: bool,
        _extended: bool,
        drop_event: bool) -> QMimeData:
    if internal or should_paste_raw():
        return mime

    if config["drag_and_drop"] and drop_event:
        return convert_mime(mime, editor_web_view.editor, action=ShowOptions.drag_and_drop)

    if config["copy_paste"] and not drop_event and (mime.hasImage() or has_local_file(mime)):
        return convert_mime(mime, editor_web_view.editor, action=ShowOptions.menus)

    return mime


def init():
    gui_hooks.editor_will_process_mime.append(on_process_mime)

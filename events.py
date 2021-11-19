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

from anki.hooks import wrap
from aqt import mw
from aqt.editor import EditorWebView

from .common import *
from .config import config
from .utils.gui import ShowOptions
from .utils.webp import ImageConverter, CanceledPaste, InvalidInput


def drop_event(editor: EditorWebView, event: QDropEvent, _old: Callable):
    if config.get("drag_and_drop") is False:
        # the feature is disabled by the user
        return _old(editor, event)

    if event.source():
        # don't filter html from other fields
        return _old(editor, event)

    # grab cursor position before it's moved by the user
    p = editor.editor.web.mapFromGlobal(QCursor.pos())

    w = ImageConverter(editor.editor, ShowOptions.drag_and_drop)
    try:
        w.convert(event.mimeData())

        def paste_field(_):
            insert_image_html(editor.editor, w.filename)
            editor.activateWindow()  # Fix for windows users

        editor.editor.web.evalWithCallback(f"focusIfField({p.x()}, {p.y()});", paste_field)
        tooltip_filesize(w.filepath)
    except InvalidInput:
        return _old(editor, event)
    except CanceledPaste as ex:
        tooltip(str(ex))
    except RuntimeError as ex:
        tooltip(str(ex))
        return _old(editor, event)
    except FileNotFoundError:
        tooltip("File not found.")
        return _old(editor, event)


def paste_event(editor: EditorWebView, _old: Callable):
    if config.get("copy_paste") is False:
        # the feature is disabled by the user
        return _old(editor)

    mime: QMimeData = mw.app.clipboard().mimeData()

    if mime.html().startswith("<!--anki-->"):
        # no filtering required for internal pastes
        return _old(editor)

    if not (mime.hasImage() or has_local_file(mime)):
        # no image was copied
        return _old(editor)

    w = ImageConverter(editor.editor, ShowOptions.menus)
    try:
        w.convert(mime)
        insert_image_html(editor.editor, w.filename)
        tooltip_filesize(w.filepath)
    except CanceledPaste as ex:
        tooltip(str(ex))
    except InvalidInput:
        return _old(editor)
    except RuntimeError as ex:
        tooltip(str(ex))
        return _old(editor)
    except FileNotFoundError:
        tooltip("File not found.")
        return _old(editor)


def init():
    EditorWebView.dropEvent = wrap(EditorWebView.dropEvent, drop_event, 'around')
    EditorWebView.onPaste = custom_decorate(EditorWebView.onPaste, paste_event)

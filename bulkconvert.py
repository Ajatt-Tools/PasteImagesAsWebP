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
from typing import Optional, Generator, Sequence, Set, Iterable, Dict, Any

from aqt import mw, gui_hooks
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import tooltip

from .utils.gui import SettingsDialog
from .utils.webp import ImageConverter


def checkpoint(msg="Checkpoint"):
    def decorator(fn):
        def decorated(*args, **kwargs):
            mw.checkpoint(msg)
            mw.progress.start()
            fn(*args, **kwargs)
            mw.progress.finish()
            mw.reset()

        return decorated

    return decorator


def find_eligible_images(html: str) -> Generator[str, None, None]:
    images = re.findall(r'<img[^>]*src="([^"]+)"[^>]*>', html)
    return (image for image in images if image[-5:] != '.webp')


def find_images_to_convert_and_notes(note_ids: Iterable) -> Dict[str, Set[Any]]:
    to_convert = {}

    for note in {mw.col.getNote(note_id) for note_id in note_ids}:
        note_content = ''.join(note.values())
        if '<img' not in note_content:
            continue
        for filename in find_eligible_images(note_content):
            to_convert[filename] = to_convert.get(filename, set()).union({note.id, })

    return to_convert


def convert_image(filename: str) -> Optional[str]:
    try:
        w = ImageConverter()
        w.load_internal(filename)
        w.convert_internal(filename)
    except RuntimeError:
        tooltip(f"Couldn't convert {filename}.")
    else:
        return w.filename


@checkpoint(msg="Bulk-convert to WebP")
def bulk_convert(note_ids: Sequence):
    to_convert = find_images_to_convert_and_notes(note_ids)

    converted = {}
    for filename in to_convert:
        if converted_filename := convert_image(filename):
            converted[filename] = converted_filename

    for initial_filename, converted_filename in converted.items():
        for note_id in to_convert[initial_filename]:
            note = mw.col.getNote(note_id)
            for key in note.keys():
                note[key] = note[key].replace(initial_filename, converted_filename)
            note.flush()

    tooltip(f"Done. Converted {len(converted)} files.")


def on_bulk_convert(browser: Browser):
    selected_notes = browser.selectedNotes()
    if selected_notes:
        dialog = SettingsDialog(browser)
        dialog.exec_()
        bulk_convert(selected_notes)
    else:
        tooltip("No cards selected.")


def setup_menu(browser: Browser):
    a = QAction("Bulk-convert to WebP", browser)
    a.triggered.connect(lambda: on_bulk_convert(browser))
    browser.form.menuEdit.addSeparator()
    browser.form.menuEdit.addAction(a)


def init():
    gui_hooks.browser_menus_did_init.append(setup_menu)

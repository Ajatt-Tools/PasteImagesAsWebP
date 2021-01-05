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

import os
import random
import subprocess
import time
from distutils.spawn import find_executable

from anki.utils import isWin

from ..config import config
from ..consts import ADDON_PATH


def find_cwebp():
    exe = find_executable('cwebp')
    if exe is None:
        # https://developers.google.com/speed/webp/download
        support_dir = "support"
        if isWin:
            exe = os.path.join(ADDON_PATH, support_dir, "cwebp.exe")
        else:
            exe = os.path.join(ADDON_PATH, support_dir, "cwebp")
            os.chmod(exe, 0o755)
    return exe


def construct_filename(target_dir_path: str):
    """Returns a unique (filename, filepath) for the new webp image"""

    def new_filename() -> str:
        return f"paste_{int(time.time())}{random.randint(100, 999)}.webp"

    def make_full_path(name) -> str:
        return os.path.join(target_dir_path, name)

    out_filename: str = new_filename()
    while os.path.isfile(make_full_path(out_filename)):
        out_filename = new_filename()

    return out_filename, make_full_path(out_filename)


def get_resize_args():
    if not (config['image_width'] == 0 and config['image_height'] == 0):
        return ['-resize', config['image_width'], config['image_height']]
    else:
        return []


def stringify_args(args: list) -> list:
    return [str(arg) for arg in args]


def convert_file(source_path: str, destination_path: str) -> bool:
    args = [cwebp, source_path, '-o', destination_path, '-q', config.get('image_quality')]
    args.extend(config.get('cwebp_args', []))
    args.extend(get_resize_args())

    p = subprocess.Popen(stringify_args(args),
                         shell=False,
                         bufsize=-1,
                         universal_newlines=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT,
                         startupinfo=si)
    stdout = p.communicate()[0]
    if p.wait() != 0:
        print(f"cwebp failed.")
        print(f"exit code = {p.returncode}")
        print(stdout)
        return False

    return True


cwebp = find_cwebp()

if isWin:
    # Prevents a console window from popping up on Windows
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    si = None

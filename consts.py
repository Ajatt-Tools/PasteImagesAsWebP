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

ADDON_PATH = os.path.dirname(__file__)
ADDON_NAME = "Paste Images As WebP"

GITHUB_LINK = "https://github.com/Ajatt-Tools/PasteImagesAsWebP"
PATREON_LINK = "https://www.patreon.com/tatsumoto_ren"
OTHER_ADDONS = "https://ankiweb.net/shared/byauthor/1425504015"
CHAT_LINK = "https://tatsumoto-ren.github.io/blog/join-our-community.html"

WINDOW_MIN_WIDTH = 400
BUTTON_MIN_HEIGHT = 29
ICON_SIDE_LEN = 17
SLIDER_STEP = 5
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')

REQUEST_HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'}
REQUEST_TIMEOUTS = (3.05, 12.05)

ABOUT_MSG = f"""\
If <b>{ADDON_NAME}</b> or any of my <a href="{OTHER_ADDONS}">other addons</a>
have been useful to you, please consider supporting me on <a href="{PATREON_LINK}">Patreon</a>.
It allows me to put more time and focus into developing them. Thanks so much!
<br><br>
If you have any questions/issues, or if you want to learn Japanese with us,
join <a href="{CHAT_LINK}">our study room</a>.
<br>
If you want to study the source code of this add-on and change it to make the add-on do what you wish,
explore the <a href="{GITHUB_LINK}">repository on github</a>.\
"""

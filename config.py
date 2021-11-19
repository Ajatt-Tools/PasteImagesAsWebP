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

from aqt import mw


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__) or dict()
    cfg['avoid_upscaling']: bool = cfg.get('avoid_upscaling', True)
    cfg['show_context_menu_entry']: bool = cfg.get('show_context_menu_entry', True)
    cfg['show_editor_button']: bool = cfg.get('show_editor_button', True)
    cfg['shortcut']: str = cfg.get('shortcut', 'Ctrl+Meta+v')
    cfg['image_width']: int = cfg.get('image_width', 0)
    cfg['image_height']: int = cfg.get('image_height', 200)
    cfg['image_quality']: str = cfg.get('image_quality', 20)
    cfg['show_settings']: str = cfg.get('show_settings', 'toolbar')
    cfg["drag_and_drop"]: bool = cfg.get('drag_and_drop', True)
    cfg['copy_paste']: bool = cfg.get('copy_paste', False)
    cfg['max_image_width']: int = cfg.get('max_image_width', 800)
    cfg['max_image_height']: int = cfg.get('max_image_height', 600)

    return cfg


def write_config():
    mw.addonManager.writeConfig(__name__, config)


config = get_config()

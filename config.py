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

from typing import Iterable

from .ajt_common.addon_config import AddonConfigManager, set_config_update_action
from .utils.show_options import ShowOptions


class PasteImagesAsWebPConfig(AddonConfigManager):
    def __init__(self):
        super().__init__()
        set_config_update_action(self.update_from_addon_manager)

    def show_settings(self) -> list[ShowOptions]:
        instances = []
        for name in self['show_settings'].split(','):
            try:
                instances.append(ShowOptions[name])
            except KeyError:
                continue
        return instances

    def set_show_options(self, options: Iterable[ShowOptions]):
        self['show_settings'] = ','.join(option.name for option in options)


config = PasteImagesAsWebPConfig()

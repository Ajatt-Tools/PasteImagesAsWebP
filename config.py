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
from aqt.utils import showCritical

from .ajt_common.addon_config import AddonConfigManager


def addon_name():
    return __name__.split(".")[0]


class PasteImagesAsWebPConfig(AddonConfigManager):
    def dict_copy(self):
        return self._config.copy()

    def update_from_addon_manager(self, new_conf: dict):
        try:
            # Config has been already written to disk by aqt.addons.ConfigEditor
            self.update(new_conf, clear_old=True)
        except RuntimeError as ex:
            showCritical(str(ex), parent=mw, help=None)  # type: ignore
            # Restore previous config.
            self.write_config()


config = PasteImagesAsWebPConfig()
mw.addonManager.setConfigUpdatedAction(addon_name(), config.update_from_addon_manager)

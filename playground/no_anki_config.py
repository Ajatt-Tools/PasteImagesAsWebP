# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import copy
import json
import pathlib

from media_converter.config import MediaConverterConfig


class NoAnkiConfigView(MediaConverterConfig):
    """
    Loads the default config without starting Anki.
    """

    config_json_path = pathlib.Path(__file__).parent.parent / "media_converter" / "config.json"

    def _set_underlying_dicts(self) -> None:
        """Load editable settings without sharing their mutable values with defaults.

        https://github.com/Ajatt-Tools/autocopy/blob/981ecb2bfae777f9b45e83e1b34e77339ca7d329/playground/no_anki_config.py#L14-L19
        """
        with open(self.config_json_path, encoding="utf-8") as f:
            self._default_config = json.load(f)
        # Standalone editing must preserve defaults and allow the normal dict_copy() API.
        self._config = copy.deepcopy(self._default_config)

    def write_config(self) -> None:
        print("write requested. doing nothing. config contents:")
        print(json.dumps(self._config, indent=4, ensure_ascii=False))

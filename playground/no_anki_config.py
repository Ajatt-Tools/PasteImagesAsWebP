import json
import pathlib

from media_converter.config import MediaConverterConfig


class NoAnkiConfigView(MediaConverterConfig):
    """
    Loads the default config without starting Anki.
    """

    config_json_path = pathlib.Path(__file__).parent.parent / "media_converter" / "config.json"

    def _set_underlying_dicts(self) -> None:
        with open(self.config_json_path) as f:
            self._default_config = self._config = json.load(f)

    def write_config(self) -> None:
        print("write requested. doing nothing.")

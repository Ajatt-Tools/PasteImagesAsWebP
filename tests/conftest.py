# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import json
import pathlib

import pytest

import media_converter.config


class NoAnkiConfigView(media_converter.config.MediaConverterConfig):
    """
    Loads the default config without starting Anki.
    """

    config_json_path = pathlib.Path(__file__).parent.parent / "media_converter" / "config.json"

    def _set_underlying_dicts(self) -> None:
        with open(self.config_json_path) as f:
            self._default_config = self._config = json.load(f)


@pytest.fixture(autouse=True)
def no_anki_config(monkeypatch):
    monkeypatch.setattr(media_converter.config, "config", NoAnkiConfigView(), raising=False)
    from media_converter.config import config

    assert config.image_extension == ".webp"

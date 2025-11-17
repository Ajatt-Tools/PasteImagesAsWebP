# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

import media_converter.config
from playground.no_anki_config import NoAnkiConfigView


@pytest.fixture(autouse=True, scope="function")
def no_anki_config() -> NoAnkiConfigView:
    config = NoAnkiConfigView()
    assert config.image_extension == ".webp"
    return config


@pytest.fixture(autouse=True, scope="function")
def no_anki_config_mp(no_anki_config, monkeypatch):
    monkeypatch.setattr(media_converter.config, "config", no_anki_config, raising=False)
    monkeypatch.setattr(media_converter.config, "get_global_config", lambda: no_anki_config, raising=False)
    return no_anki_config

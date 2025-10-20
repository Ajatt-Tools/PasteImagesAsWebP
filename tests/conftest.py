# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

import media_converter.config
from playground.no_anki_config import NoAnkiConfigView


@pytest.fixture(autouse=True, scope="function")
def no_anki_config(monkeypatch):
    config = NoAnkiConfigView()
    monkeypatch.setattr(media_converter.config, "config", config, raising=False)
    monkeypatch.setattr(media_converter.config, "get_global_config", lambda: config, raising=False)
    assert config.image_extension == ".webp"
    return config

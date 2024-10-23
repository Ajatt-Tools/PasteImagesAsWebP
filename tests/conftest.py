# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

import media_converter.config
from playground.no_anki_config import NoAnkiConfigView


@pytest.fixture(autouse=True)
def no_anki_config(monkeypatch):
    monkeypatch.setattr(media_converter.config, "config", NoAnkiConfigView(), raising=False)
    from media_converter.config import config

    assert config.image_extension == ".webp"

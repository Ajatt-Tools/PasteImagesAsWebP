# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from aqt.qt import QApplication

import media_converter.config
from playground.no_anki_config import NoAnkiConfigView


@pytest.fixture(autouse=True, scope="session")
def qapp() -> QApplication:
    """Ensure a QApplication exists for widget tests."""
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture(autouse=True, scope="function")
def no_anki_config() -> NoAnkiConfigView:
    config = NoAnkiConfigView()
    assert config.image_extension == ".webp"
    return config


@pytest.fixture(autouse=True, scope="function")
def no_anki_config_mp(no_anki_config, monkeypatch):
    monkeypatch.setattr(media_converter.config, "get_global_config", lambda: no_anki_config, raising=False)
    return no_anki_config

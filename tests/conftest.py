# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os

import pytest
from aqt.qt import QApplication

import media_converter.config
from playground.no_anki_config import NoAnkiConfigView


@pytest.fixture(scope="session", autouse=True)
def qt_offscreen_platform() -> None:
    """
    Force Qt to run without a real display so widget tests work in headless CI.
    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L22
    """
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def qapp(qt_offscreen_platform: None) -> QApplication:
    """Ensure a QApplication exists for widget tests.

    A program name must be present in argv because QtWebEngine aborts
    when QApplication is created with an empty argument list.

    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L28
    """
    match instance := QApplication.instance():
        case None:
            return QApplication(["pytest"])  # argv can't be empty
        case QApplication():
            return instance
        case _:
            raise RuntimeError("A QCoreApplication already exists; widget tests require QApplication")


@pytest.fixture(autouse=True, scope="function")
def no_anki_config() -> NoAnkiConfigView:
    config = NoAnkiConfigView()
    assert config.image_extension == ".webp"
    return config


@pytest.fixture(autouse=True, scope="function")
def no_anki_config_mp(no_anki_config, monkeypatch) -> NoAnkiConfigView:
    monkeypatch.setattr(media_converter.config, "get_global_config", lambda: no_anki_config, raising=False)
    return no_anki_config

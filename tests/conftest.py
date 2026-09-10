# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import os
import sys
import traceback
from collections.abc import Iterator
from unittest.mock import create_autospec, patch

import pytest
from aqt.browser import Browser
from aqt.editor import Editor
from aqt.qt import QApplication
from beartype import beartype

import media_converter.config
from media_converter.bulk_convert.convert_task import ConvertTask
from playground.no_anki_config import NoAnkiConfigView


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Runtime-check collected tests after Pytest has rewritten their imports.
    https://github.com/beartype/beartype
    https://github.com/Ajatt-Tools/lancet/blob/a306fd1774f2b3a70a0f836bab1135d66f4741f2/tests/conftest.py#L11
    """
    for item in items:
        if isinstance(item, pytest.Function):
            item.obj = beartype(item.obj)


@pytest.fixture(scope="session", autouse=True)
def qt_offscreen_platform() -> None:
    """
    Default Qt to a display-free platform so widget tests work in headless CI.
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
            raise RuntimeError("A QCoreApplication already exists. Widget tests require QApplication")


@pytest.fixture
def browser() -> Browser:
    """Provide typed Anki collaborators without constructing the real Browser UI.

    https://github.com/Ajatt-Tools/autocopy/blob/981ecb2bfae777f9b45e83e1b34e77339ca7d329/tests/helpers.py#L28-L40
    """
    browser = create_autospec(Browser, instance=True)
    browser.editor = create_autospec(Editor, instance=True)
    return browser


@pytest.fixture
def empty_convert_task(browser: Browser, no_anki_config: NoAnkiConfigView) -> ConvertTask:
    """Create an initialized task without searching a running Anki collection."""
    with patch.object(ConvertTask, "_find_files_to_convert_and_notes", return_value={}):
        return ConvertTask(browser, [], [], no_anki_config)


@pytest.fixture(autouse=True)
def no_qt_callback_errors() -> Iterator[None]:
    """Fail with full tracebacks when Qt reports an unhandled Python callback exception."""
    errors: list[str] = []
    # Qt can report a callback failure without propagating it to the triggering click or emit call.
    # Keep our hook independent of test monkeypatch teardown and avoid retaining traceback frames.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            sys,
            "excepthook",
            lambda kind, error, tb: errors.append("".join(traceback.format_exception(kind, error, tb))),
        )
        yield
        if errors:
            pytest.fail("Unhandled Qt callback exceptions:\n" + "\n".join(errors), pytrace=False)


@pytest.fixture(autouse=True, scope="function")
def no_anki_config(no_qt_callback_errors: None) -> NoAnkiConfigView:
    config = NoAnkiConfigView()
    assert config.image_extension == ".webp"
    return config


@pytest.fixture(autouse=True, scope="function")
def no_anki_config_mp(no_anki_config, monkeypatch) -> NoAnkiConfigView:
    monkeypatch.setattr(media_converter.config, "get_global_config", lambda: no_anki_config, raising=False)
    return no_anki_config

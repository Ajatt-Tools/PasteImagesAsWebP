# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import MagicMock, create_autospec, patch

import pytest
from aqt.browser import Browser
from aqt.editor import Editor, EditorWebView
from aqt.forms.browser import Ui_Dialog
from aqt.qt import QAction, QDialog, QMenu, QWidget

from media_converter import bulkconvert, menus
from media_converter.config import MediaConverterConfig
from media_converter.dialogs.main_settings_dialog import AnkiMainSettingsDialog
from media_converter.utils.show_options import ShowOptions


@pytest.mark.parametrize(
    "modal, expect_executed, expect_shown, expected_result",
    [
        (True, True, False, QDialog.DialogCode.Accepted),
        (False, False, True, QDialog.DialogCode.Rejected),
    ],
    ids=["addon_config_button_is_modal", "menu_action_is_non_modal"],
)
def test_open_media_converter_settings_modality(
    monkeypatch: pytest.MonkeyPatch,
    no_anki_config: MediaConverterConfig,
    modal: bool,
    expect_executed: bool,
    expect_shown: bool,
    expected_result: QDialog.DialogCode,
) -> None:
    """The menu path must stay non-modal while Anki's config button opens a modal dialog."""
    dialog = create_autospec(AnkiMainSettingsDialog, instance=True)
    dialog.exec.return_value = QDialog.DialogCode.Accepted
    dialog_class = MagicMock(return_value=dialog)
    monkeypatch.setattr(menus, "AnkiMainSettingsDialog", dialog_class)
    # A real parent respects both the runtime annotation and Qt's ownership contract.
    parent = QWidget()

    result = menus.open_media_converter_settings(no_anki_config, parent=parent, modal=modal)

    dialog_class.assert_called_once_with(no_anki_config, parent)
    assert dialog.exec.called == expect_executed
    assert dialog.show.called == expect_shown
    assert result == expected_result


class TestActionSignals:
    """Trigger real menu actions to catch signal argument mismatches under beartype."""

    @pytest.mark.parametrize("checked", [False, True])
    def test_deduplicate_action(self, no_anki_config: MediaConverterConfig, checked: bool) -> None:
        """Deduplicate takes no arguments even when QAction emits its checked flag."""
        root = QMenu()
        with patch.object(menus, "menu_root_entry", return_value=root):
            with patch.object(menus, "set_config_action", autospec=True):
                with patch.object(menus, "run_media_deduplication", autospec=True) as deduplicate:
                    menus.setup_mainwindow_menu(no_anki_config)
                    action = root.actions()[1]
                    action.setCheckable(True)
                    action.setChecked(not checked)
                    action.trigger()
        deduplicate.assert_called_once_with()

    @pytest.mark.parametrize("checked", [False, True])
    def test_bulk_convert_action(self, no_anki_config: MediaConverterConfig, browser: Browser, checked: bool) -> None:
        """Bulk conversion reaches selection handling without accepting QAction's checked flag."""
        action = QAction("Bulk convert")
        browser.selectedNotes.return_value = []
        # The real QAction needs a native Qt parent, not an autospecced Browser.
        browser.form = create_autospec(Ui_Dialog, instance=True)
        browser.form.menuEdit = QMenu()
        with patch.object(bulkconvert, "QAction", return_value=action):
            with patch.object(bulkconvert, "get_global_config", return_value=no_anki_config):
                with patch.object(bulkconvert, "tooltip", autospec=True) as notify:
                    bulkconvert.setup_menu(browser)
                    action.setCheckable(True)
                    action.setChecked(not checked)
                    action.trigger()
        browser.selectedNotes.assert_called_once_with()
        notify.assert_called_once_with(
            "No cards selected.", period=no_anki_config.tooltip_duration_milliseconds, parent=browser
        )

    @pytest.mark.parametrize("checked", [False, True])
    def test_editor_context_action(self, no_anki_config: MediaConverterConfig, checked: bool) -> None:
        """The context action keeps its bound editor without forwarding QAction's checked flag."""
        no_anki_config["show_context_menu_entry"] = True
        controller = menus.EditorMenus(no_anki_config)
        webview = create_autospec(EditorWebView, instance=True)
        webview.editor = create_autospec(Editor, instance=True)
        menu = QMenu()
        with patch.object(controller, "_convert_and_insert", autospec=True) as convert:
            controller.add_context_menu_entry(webview, menu)
            action = menu.actions()[0]
            action.setCheckable(True)
            action.setChecked(not checked)
            action.trigger()
        convert.assert_called_once_with(editor=webview.editor, source=ShowOptions.paste)

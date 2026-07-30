# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import MagicMock, create_autospec

import pytest
from aqt.qt import QDialog

from media_converter import menus
from media_converter.config import MediaConverterConfig
from media_converter.dialogs.main_settings_dialog import AnkiMainSettingsDialog


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

    result = menus.open_media_converter_settings(no_anki_config, parent=None, modal=modal)

    dialog_class.assert_called_once_with(no_anki_config, None)
    assert dialog.exec.called == expect_executed
    assert dialog.show.called == expect_shown
    assert result == expected_result

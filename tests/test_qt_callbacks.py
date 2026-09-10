# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import create_autospec, patch

import pytest
from aqt.addons import ConfigEditor
from aqt.qt import QDialog, QPushButton, Qt, QWidget

from media_converter.ajt_common.checkable_combobox import CheckableComboBox
from media_converter.config import MediaConverterConfig
from media_converter.dialogs import main_settings_dialog
from media_converter.widgets.scale_settings_widget import ScaleSettings


class TestScaleButtons:
    """Keep each loop-created scale callback bound to its own numeric factor."""

    @pytest.mark.parametrize("index", [0, 1, 2, 3, 4, 5])
    @pytest.mark.parametrize("checked", [False, True])
    def test_bound_factor(self, no_anki_config: MediaConverterConfig, index: int, checked: bool) -> None:
        """Click a real scale button without confusing its factor with the emitted checked flag."""
        settings = ScaleSettings(no_anki_config, "Scale")
        emitted: list[float] = []
        settings.factor_changed.connect(emitted.append)
        buttons = settings.findChildren(QPushButton)
        buttons[index].setCheckable(True)
        buttons[index].setChecked(not checked)
        buttons[index].click()
        assert emitted == [(0.25, 0.5, 0.75, 1.0, 1.5, 2.0)[index]]


class TestModelSignals:
    """Model-driven updates must discard index and role arguments before refreshing text."""

    @pytest.mark.parametrize("checked", [False, True])
    def test_checked_text(self, checked: bool) -> None:
        """Checking an item through the real model refreshes the combo's displayed text."""
        combo = CheckableComboBox()
        combo.addCheckableText("Front")
        combo.setCheckedTexts(["Front"])
        if not checked:
            combo.setCheckedTexts([])
        expected = ""
        if checked:
            expected = "Front"
        assert combo.currentText() == expected

    @pytest.mark.parametrize("initially_checked", [False, True])
    def test_pressed_index(self, initially_checked: bool) -> None:
        """The pressed signal passes a QModelIndex to the corrected runtime-checked handler."""
        combo = CheckableComboBox()
        combo.addCheckableText("Front")
        if initially_checked:
            combo.setCheckedTexts(["Front"])
        combo.view().pressed.emit(combo.model().index(0, 0))
        expected = Qt.CheckState.Checked
        if initially_checked:
            expected = Qt.CheckState.Unchecked
        assert combo.model().item(0).checkState() == expected


class TestAdvancedSettingsButton:
    """Test the advanced editor boundary without launching a second application window."""

    @pytest.mark.parametrize("checked", [False, True])
    def test_open_editor(self, no_anki_config: MediaConverterConfig, checked: bool) -> None:
        """The button opens the config editor without forwarding the clicked checked flag."""
        parent = QWidget()
        dialog = main_settings_dialog.AnkiMainSettingsDialog(no_anki_config, parent)
        editor = create_autospec(ConfigEditor, instance=True)
        editor_signals = QDialog()
        editor.accepted = editor_signals.accepted
        buttons = [button for button in dialog.button_box.buttons() if button.text() == "Advanced"]
        assert len(buttons) == 1
        with patch.object(main_settings_dialog, "ConfigEditor", autospec=True, return_value=editor) as constructor:
            buttons[0].setCheckable(True)
            buttons[0].setChecked(not checked)
            buttons[0].click()
        constructor.assert_called_once_with(dialog, main_settings_dialog.THIS_ADDON_MODULE, no_anki_config.dict_copy())

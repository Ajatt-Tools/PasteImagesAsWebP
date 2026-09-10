# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import patch

import pytest
from aqt.qt import QColor

from media_converter.ajt_common.color_picker import ColorEdit, ColorEditPicker


class TestColorEditPicker:
    """Verify the shared widget's new color-change signal through its public behavior."""

    @pytest.mark.parametrize("source", ["setter", "text_edit"])
    @pytest.mark.parametrize("color", ["red", "#8044AA22"])
    def test_color_changed(self, source: str, color: str) -> None:
        """Programmatic and typed changes emit the current color once per actual change."""
        picker = ColorEditPicker("black")
        emitted: list[str] = []
        picker.color_changed.connect(emitted.append)
        if source == "setter":
            picker.set_color(color)
            picker.set_color(color)
        else:
            edit = picker.findChild(ColorEdit)
            assert edit is not None
            edit.setText(color)
            edit.setText(color)
        assert picker.color_hex() == color
        assert emitted == [color]

    @pytest.mark.parametrize("accepted", [False, True])
    def test_color_dialog(self, accepted: bool) -> None:
        """An accepted color emits a change while canceling leaves the original color intact."""
        picker = ColorEditPicker("black")
        emitted: list[str] = []
        picker.color_changed.connect(emitted.append)
        chosen = QColor()
        if accepted:
            chosen = QColor("#8044AA22")
        with patch("media_converter.ajt_common.color_picker.QColorDialog.getColor", return_value=chosen):
            picker.choose_color()
        if accepted:
            assert picker.color_hex() == "#8044AA22"
            assert emitted == ["#8044AA22"]
        else:
            assert picker.color_hex() == "black"
            assert emitted == []

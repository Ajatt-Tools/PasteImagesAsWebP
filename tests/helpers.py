# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import patch

from aqt.qt import QVBoxLayout, QWidget
from beartype import beartype

from media_converter.ajt_common import about_menu


@beartype
def make_about_dialog(parent: QWidget) -> about_menu.AboutDialog:
    """Construct a real dialog without starting Chromium or requiring Anki UI services.

    https://github.com/Ajatt-Tools/autocopy/blob/981ecb2bfae777f9b45e83e1b34e77339ca7d329/tests/test_about_dialog.py#L15-L20
    """
    # Keep dialog initialization and geometry handling real while replacing the webview boundary.
    with patch.object(about_menu, "tweak_window", autospec=True):
        with patch.object(about_menu.AboutDialog, "make_root_layout", return_value=QVBoxLayout()):
            return about_menu.AboutDialog(parent)

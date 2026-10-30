# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from unittest.mock import create_autospec, patch

import pytest
from aqt.qt import QDialog, QPushButton, QWidget
from aqt.webview import AnkiWebView

from media_converter.ajt_common import about_menu, restore_geom_dialog
from tests.helpers import make_about_dialog


class TestAboutDialog:
    """Cover the geometry-aware dialog and stable webview identity.

    https://github.com/Ajatt-Tools/autocopy/blob/981ecb2bfae777f9b45e83e1b34e77339ca7d329/tests/test_about_dialog.py#L23-L52
    """

    @pytest.mark.parametrize("active_profile", [False, True])
    @pytest.mark.parametrize("operation", ["show", "exec", "accept", "reject"])
    def test_geometry_lifecycle(self, active_profile: bool, operation: str) -> None:
        """Restore and save geometry only when Anki profile storage is available."""
        parent = QWidget()
        with patch.object(restore_geom_dialog, "can_access_geom_data", return_value=active_profile):
            with patch.object(restore_geom_dialog, "restoreGeom", autospec=True) as restore:
                with patch.object(restore_geom_dialog, "saveGeom", autospec=True) as save:
                    # A modal event loop would block the test. Geometry handling remains real.
                    with patch.object(QDialog, "exec", return_value=QDialog.DialogCode.Accepted):
                        dialog = make_about_dialog(parent)
                        getattr(dialog, operation)()
        restore_count = 0
        if active_profile:
            restore_count = 1 + int(operation == "show" or operation == "exec")
        assert restore.call_args_list == [((dialog, "ajt__about_dialog"), {"adjustSize": True})] * restore_count
        save_count = int(active_profile and (operation == "accept" or operation == "reject"))
        assert save.call_args_list == [((dialog, "ajt__about_dialog"), {})] * save_count

    @pytest.mark.parametrize("html", ["", "<p>About</p>"])
    def test_webview_identity(self, html: str) -> None:
        """Assign the persistent dialog identity to the embedded webview."""
        parent = QWidget()
        dialog = make_about_dialog(parent)
        webview = create_autospec(AnkiWebView, instance=True)
        with patch.object(about_menu, "AnkiWebView", autospec=True, return_value=webview) as constructor:
            assert dialog.make_about_webview(html) is webview
        constructor.assert_called_once_with(parent=dialog)
        webview.setObjectName.assert_called_once_with("ajt__about_dialog")

    @pytest.mark.parametrize("checked", [False, True])
    def test_ok_button(self, checked: bool) -> None:
        """Clicking OK accepts the dialog without forwarding the button's checked flag."""
        parent = QWidget()
        dialog = make_about_dialog(parent)
        buttons = dialog.make_button_box()
        button = buttons.itemAt(0).widget()
        assert isinstance(button, QPushButton)
        button.setCheckable(True)
        button.setChecked(not checked)
        button.click()
        assert dialog.result() == QDialog.DialogCode.Accepted

    @pytest.mark.parametrize(
        ("index", "label", "link"),
        [(2, "Join our community", about_menu.COMMUNITY_LINK), (3, "Donate", about_menu.DONATE_LINK)],
    )
    @pytest.mark.parametrize("checked", [False, True])
    def test_link_button(self, index: int, label: str, link: str, checked: bool) -> None:
        """Each link button opens its own destination without forwarding the checked flag."""
        parent = QWidget()
        dialog = make_about_dialog(parent)
        with patch.object(about_menu, "openLink", autospec=True) as open_link:
            buttons = dialog.make_button_box()
            button = buttons.itemAt(index).widget()
            assert isinstance(button, QPushButton)
            button.setCheckable(True)
            button.setChecked(not checked)
            button.click()
        assert button.text() == label
        assert button.icon().isNull() is False
        assert button.iconSize().width() == about_menu.ICON_SIDE_LEN
        assert button.iconSize().height() == about_menu.ICON_SIDE_LEN
        assert button.minimumHeight() == about_menu.BUTTON_HEIGHT
        assert button.maximumHeight() == about_menu.BUTTON_HEIGHT
        open_link.assert_called_once_with(link)

    @pytest.mark.parametrize("checked", [False, True])
    def test_about_action(self, checked: bool) -> None:
        """The real About action opens and executes a dialog without receiving the checked flag."""
        parent = QWidget()
        dialog = make_about_dialog(parent)
        with patch.object(about_menu, "AboutDialog", autospec=True, return_value=dialog):
            with patch.object(QDialog, "exec", return_value=QDialog.DialogCode.Accepted) as execute:
                action = about_menu.create_about_action(parent)
                action.setCheckable(True)
                action.setChecked(not checked)
                action.trigger()
        execute.assert_called_once_with()

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import itertools
from collections.abc import Iterable

from anki.notes import Note
from aqt import mw
from aqt.browser import Browser
from aqt.utils import showInfo

from ..ajt_common.restore_geom_dialog import AnkiSaveAndRestoreGeomDialog
from ..config import MediaConverterConfig
from ..consts import ADDON_NAME_SNAKE
from ..widgets.audio_settings_widget import AudioSettings
from ..widgets.bulk_convert_settings_widget import BulkConvertSettings
from ..widgets.image_settings_widget import ImageSettings
from .settings_dialog_base import (
    SettingsDialogBase,
    SettingsTabs,
)


def get_all_keys(notes: Iterable[Note]) -> list[str]:
    """
    Returns a list of field names present in passed notes, without duplicates.
    """
    return sorted(frozenset(itertools.chain(*(note.keys() for note in notes))))


class BulkConvertDialog(SettingsDialogBase):
    """Dialog shown on bulk-convert."""

    name: str = f"ajt__{ADDON_NAME_SNAKE}_bulk_convert_dialog"
    _tabs: SettingsTabs
    _image_settings: ImageSettings
    _audio_settings: AudioSettings
    _bulk_convert_settings: BulkConvertSettings

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(config, parent)
        self._image_settings = ImageSettings(config=self.config)
        self._audio_settings = AudioSettings(config=self.config)
        self._bulk_convert_settings = BulkConvertSettings(config=self.config)
        self._tabs = SettingsTabs(self.config, self._image_settings, self._audio_settings, self._bulk_convert_settings)
        self._setup_ui()
        self.setup_bottom_button_box()
        self.set_initial_values()

    def _setup_ui(self) -> None:
        self.main_vbox.addWidget(self._tabs)
        self.main_vbox.addStretch()
        self.main_vbox.addWidget(self.button_box)

    def set_initial_values(self) -> None:
        self._image_settings.set_initial_values()
        self._audio_settings.set_initial_values()
        self._bulk_convert_settings.set_initial_values(all_field_names=self.selected_notes_fields())

    def selected_fields(self) -> list[str]:
        return self._bulk_convert_settings.field_selector.checked_texts()

    def selected_notes_fields(self) -> list[str]:
        """
        A dummy used when Anki isn't running.
        """
        assert mw is None
        return ["A", "B", "C"]

    def accept(self) -> None:
        if not self._bulk_convert_settings.field_selector.has_valid_selection():
            showInfo(title="Can't accept settings", text="No fields selected. Nothing to convert.")
            return
        self._image_settings.pass_settings_to_config()
        self._audio_settings.pass_settings_to_config()
        self._bulk_convert_settings.pass_settings_to_config()
        self.config.write_config()
        return super().accept()


class AnkiBulkConvertDialog(BulkConvertDialog, AnkiSaveAndRestoreGeomDialog):
    """
    Adds methods that work only when Anki is running.
    """

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(config, parent)

    def selected_notes_fields(self) -> list[str]:
        """
        Return a list of field names where each field name is present in at least one selected note.
        """
        browser = self.parent()
        assert mw
        assert isinstance(browser, Browser)
        return get_all_keys(mw.col.get_note(nid) for nid in browser.selectedNotes())

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import itertools
from collections.abc import Iterable

from anki.notes import Note
from aqt import mw
from aqt.browser import Browser
from aqt.qt import *
from aqt.utils import restoreGeom, saveGeom, showInfo

from ..ajt_common.multiple_choice_selector import MultipleChoiceSelector
from ..config import ImageFormat, MediaConverterConfig
from .audio_settings_widget import AudioSettings
from .image_settings_widget import ImageSettings
from .settings_dialog_base import (
    ADDON_NAME_SNAKE,
    ConfigPropMixIn,
    HasNameMixIn,
    SettingsDialogBase,
    SettingsTabs,
)


def get_all_keys(notes: Iterable[Note]) -> list[str]:
    """
    Returns a list of field names present in passed notes, without duplicates.
    """
    return sorted(frozenset(itertools.chain(*(note.keys() for note in notes))))


class EnableReconvertCheckbox(QCheckBox):
    def __init__(self, enabled_image_format: ImageFormat) -> None:
        super().__init__()
        self.setText(f"Reconvert existing {enabled_image_format.name} images")


class BulkConvertSettings(HasNameMixIn, ConfigPropMixIn):
    name = "Bulk-convert settings"
    _field_selector: MultipleChoiceSelector
    _reconvert_checkbox: QCheckBox

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._field_selector = MultipleChoiceSelector()
        self._reconvert_checkbox = EnableReconvertCheckbox(self.config.image_format)
        self._layout = QFormLayout()
        self._setup_ui()
        self._add_tooltips()

    @property
    def field_selector(self) -> MultipleChoiceSelector:
        return self._field_selector

    def _setup_ui(self) -> None:
        self._layout.addRow(self._field_selector)
        self._layout.addRow(self._reconvert_checkbox)
        self.setLayout(self._layout)

    def _add_tooltips(self) -> None:
        self._field_selector.setToolTip(
            "When enabled, search for image files only in selected fields.\n" "When disabled, search in all fields."
        )
        self._reconvert_checkbox.setToolTip(
            "If an image was converted to the target format before,\n"
            "convert it again.\n"
            "For example, change quality or dimensions."
        )

    def set_initial_values(self, all_field_names: list[str]) -> None:
        self._field_selector.set_texts(all_field_names)
        self._field_selector.set_checked_texts(self.config["bulk_convert_fields"])
        self._reconvert_checkbox.setChecked(self.config.bulk_reconvert)

    def pass_settings_to_config(self) -> None:
        self.config["bulk_convert_fields"] = self._field_selector.checked_texts()
        self.config.bulk_reconvert = self._reconvert_checkbox.isChecked()


class BulkConvertDialog(SettingsDialogBase):
    """Dialog shown on bulk-convert."""

    name = f"ajt__{ADDON_NAME_SNAKE}_bulk_convert_dialog"
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


class AnkiBulkConvertDialog(BulkConvertDialog):
    """
    Adds methods that work only when Anki is running.
    """

    def __init__(self, config: MediaConverterConfig, parent=None) -> None:
        super().__init__(config, parent)
        restoreGeom(self, self.name, adjustSize=True)

    def selected_notes_fields(self) -> list[str]:
        """
        Return a list of field names where each field name is present in at least one selected note.
        """
        browser = self.parent()
        assert mw
        assert isinstance(browser, Browser)
        return get_all_keys(mw.col.get_note(nid) for nid in browser.selectedNotes())

    def accept(self) -> None:
        saveGeom(self, self.name)
        return super().accept()

    def reject(self) -> None:
        saveGeom(self, self.name)
        return super().reject()

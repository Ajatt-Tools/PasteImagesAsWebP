# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from typing import Iterable, Optional, List

from aqt.qt import *

from .checkable_combobox import CheckableComboBox


class FieldSelector(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._combo = CheckableComboBox()
        self.setTitle("Limit to field")
        self.setCheckable(True)
        self.setChecked(False)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._combo)

    def add_fields(self, fields: Iterable[str]):
        return self._combo.addCheckableTexts(fields)

    def selected_fields(self) -> List[str]:
        return list(self._combo.checkedTexts()) if self.isChecked() else []

    def set_fields(self, fields: Optional[List[str]]):
        if fields:
            self.setChecked(True)
            self._combo.setCheckedTexts(fields)
        else:
            self.setChecked(False)

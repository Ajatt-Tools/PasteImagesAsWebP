# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import io
from typing import Optional

import aqt
from aqt.qt import *

from ..ajt_common.about_menu import tweak_window
from ..consts import ADDON_FULL_NAME
from ..bulk_convert.convert_result import ConvertResult


def fallback_parent(parent) -> Optional[QWidget]:
    if parent is None:
        try:
            return aqt.mw.app.activeWindow() or aqt.mw
        except AttributeError:
            assert aqt.mw is None
            pass
    return parent


def form_report_message(result: ConvertResult) -> str:
    buffer = io.StringIO()
    buffer.write(f"<p>Converted <code>{len(result.converted)}</code> files.</p>")
    if result.failed:
        buffer.write(f"<p>Failed <code>{len(result.failed)}</code> files.</p>")
        buffer.write("<ol>")
        for file, reason in result.failed.items():
            buffer.write(f"<li><code>{file}</code>: {reason}</li>")
        buffer.write("</ol>")
    return buffer.getvalue()


class AJTScrollLabel(QScrollArea):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        content = QWidget(self)
        self.setWidget(content)
        layout = QVBoxLayout(content)
        self._label = QLabel(content)
        self._label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self._label.setWordWrap(False)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(self._label)

    def set_text(self, text: str) -> None:
        return self._label.setText(text)


class BulkConvertResultDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=fallback_parent(parent))
        tweak_window(self)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle(f"{ADDON_FULL_NAME} - Convert Results")
        self.setSizePolicy(self.make_size_policy())
        self.setMinimumSize(320, 320)
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._label = AJTScrollLabel()
        self.setLayout(self.make_root_layout())
        qconnect(self._button_box.accepted, self.accept)

    def set_result(self, result: ConvertResult) -> None:
        self._label.set_text(form_report_message(result))

    def make_root_layout(self) -> QLayout:
        root_layout = QVBoxLayout()
        root_layout.addWidget(self._label)
        root_layout.addWidget(self._button_box)
        return root_layout

    def make_size_policy(self) -> QSizePolicy:
        size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.sizePolicy().hasHeightForWidth())
        return size_policy

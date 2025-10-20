# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import Sequence

from aqt.qt import *

from media_converter.dialogs.deduplicate_dialog import DeduplicateMediaConfirmDialog, DeduplicateTableColumns


def show_deduplication_confirm_dialog(files: Sequence[DeduplicateTableColumns]) -> DeduplicateMediaConfirmDialog:
    dialog = DeduplicateMediaConfirmDialog(column_names=DeduplicateTableColumns.column_names())
    dialog.load_data(files)
    return dialog


def make_random_files():
    return [DeduplicateTableColumns(f"zzz{idx}.jpg", "xxx.jpg") for idx in range(10)]


def main() -> None:
    app = QApplication(sys.argv)
    dialog = show_deduplication_confirm_dialog(make_random_files())
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

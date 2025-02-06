# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from media_converter.dialogs.bulk_convert_dialog import BulkConvertDialog
from playground.no_anki_config import NoAnkiConfigView


def main() -> None:
    app = QApplication(sys.argv)
    cfg = NoAnkiConfigView()
    form = BulkConvertDialog(cfg)
    form.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

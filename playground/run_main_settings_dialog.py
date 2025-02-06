# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from media_converter.widgets.main_settings_dialog import MainSettingsDialog
from playground.no_anki_config import NoAnkiConfigView


def main() -> None:
    app = QApplication(sys.argv)
    cfg = NoAnkiConfigView()
    form = MainSettingsDialog(cfg)
    form.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

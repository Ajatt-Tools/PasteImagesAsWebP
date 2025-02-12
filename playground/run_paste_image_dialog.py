# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import NamedTuple

from aqt.qt import *

from media_converter.dialogs.paste_image_dialog import PasteImageDialog
from media_converter.utils.show_options import ImageDimensions
from playground.no_anki_config import NoAnkiConfigView


def main() -> None:
    app = QApplication(sys.argv)
    cfg = NoAnkiConfigView()
    form = PasteImageDialog(cfg, dimensions=ImageDimensions(640, 480))
    form.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

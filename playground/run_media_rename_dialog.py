# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from media_converter.media_rename import MediaRenameDialog


def main() -> None:
    app = QApplication(sys.argv)
    form = MediaRenameDialog(["image_001.png", "recording.mp3", "photo.webp"])
    form.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

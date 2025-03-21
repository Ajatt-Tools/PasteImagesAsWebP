# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from aqt.qt import *

from media_converter.bulk_convert.convert_result import ConvertResult
from media_converter.dialogs.bulk_convert_result_dialog import BulkConvertResultDialog
from media_converter.file_converters.common import ConverterType, LocalFile


def fill_fake_results(result: ConvertResult):
    for idx in range(1, 1000):
        result.add_failed(LocalFile(f"image_{idx}.jpg", ConverterType.image), RuntimeError("runtime error"))


def main() -> None:
    app = QApplication(sys.argv)
    result = ConvertResult()
    fill_fake_results(result)
    dialog = BulkConvertResultDialog()
    dialog.set_result(result)
    dialog.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

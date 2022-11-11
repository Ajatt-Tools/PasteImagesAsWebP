# Copyright: Ren Tatsumoto <tatsu at autistici.org>
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

# Implementations
# https://gis.stackexchange.com/questions/350148/qcombobox-multiple-selection-pyqt5
# https://www.geeksforgeeks.org/pyqt5-checkable-combobox-showing-checked-items-in-textview/

from typing import Iterable

from aqt.qt import *


class CheckableComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initial state
        self._opened = False

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)

        # Make the lineedit the same color as QPushButton
        palette = QApplication.palette()
        palette.setBrush(QPalette.ColorRole.Base, palette.button())
        self.lineEdit().setPalette(palette)

        # Use custom delegate and model
        self.setItemDelegate(QStyledItemDelegate())
        self.setModel(QStandardItemModel(self))

        # when any item get pressed
        qconnect(self.view().pressed, self.handle_item_pressed)

        # Update the text when an item is toggled
        qconnect(self.model().dataChanged, self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def handle_item_pressed(self, index):
        """ Check the pressed item if unchecked and vice-versa """
        item: QStandardItem = self.model().itemFromIndex(index)
        item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def resizeEvent(self, event):
        """ Recompute text to elide as needed """
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent):
        if event.type() == QEvent.Type.MouseButtonRelease:
            if obj == self.lineEdit():
                self.togglePopup()
                return True
            if obj == self.view().viewport():
                return True
        return False

    def togglePopup(self):
        return self.hidePopup() if self._opened else self.showPopup()

    def showPopup(self):
        """ When the popup is displayed, a click on the lineedit should close it """
        super().showPopup()
        self._opened = True

    def hidePopup(self):
        super().hidePopup()
        self._opened = False
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        """ After timeout, kill timer, and re-enable click on line-edit """
        self.killTimer(event.timerId())
        self._opened = False

    def _set_elided_text(self, text: str):
        """ Compute elided text (with "...") """
        metrics = QFontMetrics(self.lineEdit().font())
        elided_text = metrics.elidedText(text, Qt.TextElideMode.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elided_text)

    def updateText(self):
        text = ", ".join(self.checkedTexts())
        self._set_elided_text(text)

    def addCheckableText(self, text: str):
        item = QStandardItem()
        item.setText(text)
        item.setCheckable(True)
        item.setEnabled(True)
        item.setCheckState(Qt.CheckState.Unchecked)
        self.model().appendRow(item)

    def addCheckableTexts(self, texts: Iterable[str]):
        for text in texts:
            self.addCheckableText(text)

    def items(self) -> Iterable[QStandardItem]:
        return (self.model().item(i) for i in range(self.model().rowCount()))

    def checkedItems(self) -> Iterable[QStandardItem]:
        return filter(lambda item: item.checkState() == Qt.CheckState.Checked, self.items())

    def checkedTexts(self) -> Iterable[str]:
        return map(QStandardItem.text, self.checkedItems())

    def setCheckedTexts(self, texts: Iterable[str]):
        for item in self.items():
            item.setCheckState(Qt.Checked if item.text() in texts else Qt.Unchecked)


class TestWindow(QMainWindow):
    items = (
        "Milk",
        "Eggs",
        "Butter",
        "Cheese",
        "Yogurt",
        "Chicken",
        "Fish",
        "Potatoes",
        "Carrots",
        "Onions",
        "Garlic",
        "Sugar",
        "Salt",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widget = QWidget()
        main_layout = QVBoxLayout()
        widget.setLayout(main_layout)
        self.setCentralWidget(widget)
        combo_box = CheckableComboBox()
        print_button = QPushButton('Print Values')
        main_layout.addWidget(combo_box)  # type: ignore
        main_layout.addWidget(print_button)  # type: ignore
        combo_box.addCheckableTexts(self.items)
        combo_box.setCheckedTexts(self.items[3:6])
        qconnect(print_button.clicked, lambda: print('\n'.join(combo_box.checkedTexts())))


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    window.resize(480, 320)
    app.exit(app.exec())


if __name__ == '__main__':
    main()

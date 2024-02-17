import enum


class ShowOptions(enum.Enum):
    menus = "Toolbar and menus"
    drag_and_drop = "On drag and drop"
    add_note = "Note added"
    paste = "On paste"

    def __eq__(self, other: str):
        return self.name == other

    @classmethod
    def index_of(cls, name):
        for index, item in enumerate(cls):
            if name == item.name:
                return index
        return 0


def main():
    print(ShowOptions['menus'])


if __name__ == '__main__':
    main()

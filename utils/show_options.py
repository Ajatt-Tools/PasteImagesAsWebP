import enum


class ShowOptions(enum.Enum):
    menus = "Toolbar and menus"
    drag_and_drop = "On drag and drop"
    add_note = "Note added"
    paste = "On paste"

    def __eq__(self, other: str):
        return self.name == other


def main():
    print(ShowOptions['menus'])


if __name__ == '__main__':
    main()

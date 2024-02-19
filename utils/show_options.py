import enum


class ShowOptions(enum.Enum):
    toolbar = "Toolbar"
    drag_and_drop = "On drag and drop"
    add_note = "Note added"
    paste = "On paste"


def main():
    print(ShowOptions['toolbar'])


if __name__ == '__main__':
    main()

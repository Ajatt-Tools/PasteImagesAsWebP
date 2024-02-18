import enum


class ShowOptions(enum.Enum):
    toolbar = "Toolbar"
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

    @classmethod
    def parse_variant(cls, name):
        if name == "menus":
            return cls["toolbar"]
        return cls[name]


def main():
    print(ShowOptions["toolbar"])


if __name__ == '__main__':
    main()

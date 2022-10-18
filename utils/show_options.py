import enum


class ShowOptions(enum.Enum):
    always = "Always"
    menus = "Toolbar and menus"
    drag_and_drop = "On drag and drop"
    never = "Never"

    def __eq__(self, other: str):
        return self.name == other

    @classmethod
    def index_of(cls, name):
        for index, item in enumerate(cls):
            if name == item.name:
                return index
        return 0

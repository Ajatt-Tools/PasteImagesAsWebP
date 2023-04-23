# Copyright: Ren Tatsumoto <tatsu at autistici.org> and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import abc
from typing import Protocol, Optional

from anki.notes import Note
from aqt.editor import Editor


class ImageConverter(Protocol):
    @property
    @abc.abstractmethod
    def dest_dir(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def editor(self) -> Optional[Editor]:
        ...

    @property
    @abc.abstractmethod
    def note(self) -> Optional[Note]:
        ...

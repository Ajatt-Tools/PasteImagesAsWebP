# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from media_converter.config import AudioContainer


def test_audio_container() -> None:
    assert AudioContainer("opus") == AudioContainer.opus
    assert AudioContainer("ogg") == AudioContainer.ogg
    assert AudioContainer("missing") == AudioContainer.ogg
    assert [item.name for item in AudioContainer] == ["opus", "ogg"]

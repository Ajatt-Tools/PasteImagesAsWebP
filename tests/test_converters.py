# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

def test_target_extension(no_anki_config):
    from media_converter.file_converters.common import LocalFile
    from media_converter.file_converters.internal_file_converter import get_target_extension

    assert get_target_extension(LocalFile.image("test.jpg")) == ".webp"
    assert get_target_extension(LocalFile.audio("test.mp3")) == ".ogg"

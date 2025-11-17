# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html


def test_target_extension(no_anki_config) -> None:
    from media_converter.file_converters.common import LocalFile
    from media_converter.utils.file_paths_factory import FilePathFactory

    # Create a FilePathFactory instance with the config
    fpf = FilePathFactory(note=None, editor=None, config=no_anki_config)

    assert fpf.get_target_extension(LocalFile.image("test.jpg")) == ".webp"
    assert fpf.get_target_extension(LocalFile.audio("test.mp3")) == ".ogg"

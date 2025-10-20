# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
from typing import Union

import pytest

from media_converter.utils.config_types import AudioContainer, ImageFormat


def test_audio_container() -> None:
    assert AudioContainer("opus") == AudioContainer.opus
    assert AudioContainer("ogg") == AudioContainer.ogg
    assert AudioContainer("missing") == AudioContainer.ogg
    assert [item.name for item in AudioContainer] == ["opus", "ogg"]


@pytest.mark.parametrize(
    "image_format, result_format",
    [
        ("webp", ImageFormat.webp),
        ("avif", ImageFormat.avif),
        (ImageFormat.avif, ImageFormat.avif),
        (ImageFormat.webp, ImageFormat.webp),
    ],
)
def test_set_format(no_anki_config, image_format: Union[ImageFormat, str], result_format: ImageFormat) -> None:
    no_anki_config.image_format = image_format
    assert no_anki_config.image_format == result_format
    assert no_anki_config["image_format"] == result_format.name


def test_invalid_format(no_anki_config) -> None:
    with pytest.raises(ValueError):
        no_anki_config.image_format = 1

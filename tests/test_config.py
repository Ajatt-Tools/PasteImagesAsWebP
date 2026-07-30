# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import pytest

from media_converter.utils.config_types import AudioContainer, ImageFormat


@pytest.mark.parametrize(
    "value, expected",
    [
        ("opus", AudioContainer.opus),
        ("ogg", AudioContainer.ogg),
        ("webm", AudioContainer.webm),
        ("missing", AudioContainer.ogg),
    ],
)
def test_audio_container(value: str, expected: AudioContainer) -> None:
    assert AudioContainer(value) == expected


def test_audio_container_names() -> None:
    assert [item.name for item in AudioContainer] == ["opus", "ogg", "webm"]


@pytest.mark.parametrize(
    "image_format, result_format",
    [
        ("webp", ImageFormat.webp),
        ("avif", ImageFormat.avif),
        (ImageFormat.avif, ImageFormat.avif),
        (ImageFormat.webp, ImageFormat.webp),
    ],
)
def test_set_format(no_anki_config, image_format: ImageFormat | str, result_format: ImageFormat) -> None:
    no_anki_config.image_format = image_format
    assert no_anki_config.image_format == result_format
    assert no_anki_config["image_format"] == result_format.name


def test_invalid_format(no_anki_config) -> None:
    with pytest.raises(ValueError):
        no_anki_config.image_format = 1


@pytest.mark.parametrize("include_converted", [True, False], ids=["reconvert", "normal"])
def test_video_containers_excluded_by_default(no_anki_config, include_converted: bool) -> None:
    """Video files are not images and must never be passed to the image converter."""
    excluded = no_anki_config.get_excluded_image_extensions(include_converted=include_converted)
    assert {".mp4", ".mkv"}.issubset(excluded)

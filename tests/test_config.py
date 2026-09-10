# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import copy

import pytest
from beartype.roar import BeartypeCallHintParamViolation

from media_converter.config import MediaConverterConfig
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


@pytest.mark.parametrize("invalid_format", [1, None, False])
def test_invalid_format(no_anki_config: MediaConverterConfig, invalid_format: int | None) -> None:
    """Runtime type checks reject invalid types before configuration can change."""
    original_format = no_anki_config.image_format
    with pytest.raises(BeartypeCallHintParamViolation):
        no_anki_config.image_format = invalid_format
    assert no_anki_config.image_format == original_format


@pytest.mark.parametrize("invalid_format", ["png", "missing", ""])
def test_unsupported_format(no_anki_config: MediaConverterConfig, invalid_format: str) -> None:
    """Unsupported strings reach format validation without changing configuration."""
    original_format = no_anki_config.image_format
    with pytest.raises(AssertionError, match="image format should be supported"):
        no_anki_config.image_format = invalid_format
    assert no_anki_config.image_format == original_format


@pytest.mark.parametrize("include_converted", [True, False], ids=["reconvert", "normal"])
def test_video_containers_excluded_by_default(no_anki_config, include_converted: bool) -> None:
    """Video files are not images and must never be passed to the image converter."""
    excluded = no_anki_config.get_excluded_image_extensions(include_converted=include_converted)
    assert {".mp4", ".mkv", ".mov", ".webm", ".avi"}.issubset(excluded)


class TestStandaloneConfig:
    """Keep standalone settings editable without mutating defaults or returned copies."""

    @pytest.mark.parametrize("key", ["cwebp_args", "ffmpeg_args", "bulk_convert_fields"])
    def test_detached_values(self, no_anki_config: MediaConverterConfig, key: str) -> None:
        """Nested edits leave defaults intact, and dict_copy returns independently editable settings."""
        defaults = copy.deepcopy(no_anki_config.default_config)
        no_anki_config[key].append("test-value")
        copied = no_anki_config.dict_copy()
        copied[key].append("copy-only-value")
        assert no_anki_config.is_default is False
        assert no_anki_config.default_config == defaults
        assert no_anki_config[key] == [*defaults[key], "test-value"]

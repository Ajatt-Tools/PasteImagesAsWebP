# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import re

HTML = """
<img src="1.webp">[sound:file1.ogg]
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
<img src="2.jpg">
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
<img src="3.avif">
<img src="4.png">
[sound:臣民_シンミ＼ン_3_NHK-2016.ogg]<img src="5.svg">
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
[sound:極貧_ゴクヒン━_0_NHK-2016.mp3]
[sound:極貧_ゴクヒン━_0_NHK-2016.ogg]
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
"""


def test_image_format():
    from media_converter.utils.config_types import SUPPORTED_IMAGE_FORMATS

    assert frozenset(SUPPORTED_IMAGE_FORMATS) == frozenset(["avif", "webp"])


def test_find_convertible_images(no_anki_config) -> None:
    from media_converter.common import find_convertible_images

    assert frozenset(find_convertible_images(HTML)) == frozenset(("2.jpg", "4.png"))
    assert frozenset(find_convertible_images(HTML, include_converted=True)) == frozenset(("1.webp", "2.jpg", "4.png"))

    # The config should be idiot-proof.
    no_anki_config.excluded_image_containers = ""
    # The target extension is still excluded.
    assert frozenset(find_convertible_images(HTML)) == frozenset(("2.jpg", "3.avif", "4.png", "5.svg"))
    # Reconvert enabled.
    assert frozenset(find_convertible_images(HTML, include_converted=True)) == frozenset(
        ("1.webp", "2.jpg", "3.avif", "4.png", "5.svg")
    )


def test_find_convertible_audio(no_anki_config) -> None:
    from media_converter.common import find_convertible_audio

    assert frozenset(find_convertible_audio(HTML)) == frozenset(("極貧_ゴクヒン━_0_NHK-2016.mp3",))
    assert frozenset(find_convertible_audio(HTML, include_converted=True)) == frozenset((
        "file1.ogg",
        "臣民_シンミ＼ン_3_NHK-2016.ogg",
        "極貧_ゴクヒン━_0_NHK-2016.mp3",
        "極貧_ゴクヒン━_0_NHK-2016.ogg",
    ))

    # The config should be idiot-proof.
    no_anki_config.excluded_audio_containers = ""
    # The target extension is still excluded.
    assert frozenset(find_convertible_audio(HTML)) == frozenset(("極貧_ゴクヒン━_0_NHK-2016.mp3",))
    # Reconvert enabled.
    assert frozenset(find_convertible_audio(HTML, include_converted=True)) == frozenset((
        "file1.ogg",
        "臣民_シンミ＼ン_3_NHK-2016.ogg",
        "極貧_ゴクヒン━_0_NHK-2016.mp3",
        "極貧_ゴクヒン━_0_NHK-2016.ogg",
    ))


def test_find_regex() -> None:
    from media_converter.common import RE_AUDIO_HTML_TAG, RE_IMAGE_HTML_TAG

    assert re.findall(RE_IMAGE_HTML_TAG, HTML) == [
        "1.webp",
        "2.jpg",
        "3.avif",
        "4.png",
        "5.svg",
    ]
    assert re.findall(RE_AUDIO_HTML_TAG, HTML) == [
        "file1.ogg",
        "臣民_シンミ＼ン_3_NHK-2016.ogg",
        "極貧_ゴクヒン━_0_NHK-2016.mp3",
        "極貧_ゴクヒン━_0_NHK-2016.ogg",
    ]

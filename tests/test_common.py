# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

HTML = """
<img src="1.webp">
<img src="2.jpg">
<img src="3.avif">
<img src="4.png">
<img src="5.svg">
"""


def test_find_convertible_images(no_anki_config) -> None:
    from media_converter.common import find_convertible_images
    from media_converter.config import config

    assert frozenset(find_convertible_images(HTML)) == frozenset(("2.jpg", "4.png"))
    assert frozenset(find_convertible_images(HTML, include_converted=True)) == frozenset(("1.webp", "2.jpg", "4.png"))

    # The config should be idiot-proof.
    config["excluded_image_containers"] = ""
    # The target extension is still excluded.
    assert frozenset(find_convertible_images(HTML)) == frozenset(("2.jpg", "3.avif", "4.png", "5.svg"))
    # Reconvert enabled.
    assert frozenset(find_convertible_images(HTML, include_converted=True)) == frozenset(
        ("1.webp", "2.jpg", "3.avif", "4.png", "5.svg")
    )

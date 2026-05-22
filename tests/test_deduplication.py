# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest

from media_converter.media_deduplication.deduplication import do_replacements


@pytest.mark.parametrize(
    "content, old_name, new_name, expected",
    [
        ('<img src="old.png">', "old.png", "new.png", '<img src="new.png">'),
        ("<img src='old.png'>", "old.png", "new.png", "<img src='new.png'>"),
        ('<a href="old.png">link</a>', "old.png", "new.png", '<a href="new.png">link</a>'),
        ("<a href='old.png'>link</a>", "old.png", "new.png", "<a href='new.png'>link</a>"),
        ("[sound:old.mp3]", "old.mp3", "new.ogg", "[sound:new.ogg]"),
        ('url("old.png")', "old.png", "new.png", 'url("new.png")'),
        ("url('old.png')", "old.png", "new.png", "url('new.png')"),
        ("url(old.png)", "old.png", "new.png", "url(new.png)"),
        ("url(&quot;old.png&quot;)", "old.png", "new.png", "url(&quot;new.png&quot;)"),
        ("url(&#39;old.png&#39;)", "old.png", "new.png", "url(&#39;new.png&#39;)"),
        ('<img src="other.png">', "old.png", "new.png", '<img src="other.png">'),
        ('<img src="old.png">[sound:old.png]', "old.png", "new.png", '<img src="new.png">[sound:new.png]'),
        ('<img src="ba.png">', "a.png", "new.png", '<img src="ba.png">'),
        (">old.png<", "old.png", "new.png", ">new.png<"),
        ("some old.png text", "old.png", "new.png", "some new.png text"),
    ],
    ids=[
        "src_double_quotes",
        "src_single_quotes",
        "href_double_quotes",
        "href_single_quotes",
        "sound_tag",
        "css_url_double_quotes",
        "css_url_single_quotes",
        "css_url_no_quotes",
        "css_url_html_entities_double",
        "css_url_html_entities_single",
        "no_match_unchanged",
        "multiple_occurrences",
        "substring_not_replaced",
        "plain_text_gt_lt",
        "space_surrounded",
    ],
)
def test_do_replacements(content: str, old_name: str, new_name: str, expected: str) -> None:
    assert do_replacements(content, old_name, new_name) == expected

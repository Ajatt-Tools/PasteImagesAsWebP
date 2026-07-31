# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import json
import pathlib
import re

ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
CONFIG_JSON_PATH = ROOT_DIR / "media_converter" / "config.json"
CONFIG_MD_PATH = ROOT_DIR / "media_converter" / "config.md"
CONFIG_KEY_RE = re.compile(r"^\* `(?P<key>[^`]+)`", re.MULTILINE)


class TestConfigDocs:
    def test_config_md_documents_all_config_json_keys(self) -> None:
        """Every key in config.json must be documented in config.md."""
        with open(CONFIG_JSON_PATH, encoding="utf-8") as f:
            expected_keys = set(json.load(f))
        with open(CONFIG_MD_PATH, encoding="utf-8") as f:
            documented_keys = set(CONFIG_KEY_RE.findall(f.read()))
        assert documented_keys == expected_keys

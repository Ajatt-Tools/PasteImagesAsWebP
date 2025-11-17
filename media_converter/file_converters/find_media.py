# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
import re
from collections.abc import Iterable

from ..common import RE_AUDIO_HTML_TAG, RE_IMAGE_HTML_TAG
from ..config import MediaConverterConfig
from .common import get_file_extension


class FindMedia:
    _config: MediaConverterConfig

    def __init__(self, config: MediaConverterConfig) -> None:
        self._config = config

    def is_excluded_image_extension(self, filename: str, include_converted: bool = False) -> bool:
        """
        Return true if the image file with this filename should not be converted.

        :param filename: Name of the file.
        :param include_converted: Allow reconversion. The target extension (webp, avif) will not be excluded.
        """

        return get_file_extension(filename) in self._config.get_excluded_image_extensions(include_converted)

    def is_excluded_audio_extension(self, filename: str, include_converted: bool = False) -> bool:
        """
        Return true if the audio file with this filename should not be converted.

        :param filename: Name of the file.
        :param include_converted: Allow reconversion. The target extension (webp, avif) will not be excluded.
        """

        return get_file_extension(filename) in self._config.get_excluded_audio_extensions(include_converted)

    def find_convertible_images(self, html: str, include_converted: bool = False) -> Iterable[str]:
        """
        Find image files referenced by a note.
        :param html: Note content (joined fields).
        :param include_converted: Reconvert files even if they already have been converted to the target format. E.g. to reduce size.
        :return: Filenames
        """
        if "<img" not in html:
            return
        filename: str
        for filename in re.findall(RE_IMAGE_HTML_TAG, html):
            # Check if the filename ends with any of the excluded extensions
            if not self.is_excluded_image_extension(filename, include_converted):
                yield filename

    def find_convertible_audio(self, html: str, include_converted: bool = False) -> Iterable[str]:
        """
        Find audio files referenced by a note.
        :param html: Note content (joined fields).
        :param include_converted: Reconvert files even if they already have been converted to the target format. E.g. to reduce size.
        :return: Filenames
        """
        if "[sound:" not in html:
            return
        filename: str
        for filename in re.findall(RE_AUDIO_HTML_TAG, html):
            # Check if the filename ends with any of the excluded extensions
            if not self.is_excluded_audio_extension(filename, include_converted):
                yield filename

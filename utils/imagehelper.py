import re
import urllib
from typing import Optional, Iterable
from urllib.error import URLError

from aqt.qt import *


def url_from_html_data(html):
    try:
        return re.search('(?<= src=")[^"]+(?=")', html).group(0)
    except AttributeError:
        return None


def first_url(mime: QMimeData):
    return mime.urls()[0].toString() if len(mime.urls()) > 0 else None


def q_image_from_url(src_url) -> Optional[QImage]:
    image = QImage()
    try:
        req = urllib.request.Request(src_url, None, {'User-Agent': 'Mozilla/5.0 (compatible; Anki)'})
        file_contents = urllib.request.urlopen(req).read()
        image.loadFromData(file_contents)
    except (ValueError, URLError):
        return None
    return image


def q_image_candidates(mime: QMimeData) -> Iterable[Optional[QImage]]:
    yield mime.imageData()
    yield q_image_from_url(first_url(mime))
    yield q_image_from_url(url_from_html_data(mime.html()))


def save_image(tmp_path: str, mime: QMimeData) -> bool:
    for image in q_image_candidates(mime):
        if image and image.save(tmp_path, 'png') is True:
            break
    else:
        return False

    return True

# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from typing import Optional

from aqt.qt import *
from aqt.utils import showWarning

from ..ajt_common.utils import find_executable as find_executable_ajt
from ..common import get_file_extension
from ..config import ImageFormat, MediaConverterConfig, get_global_config
from ..consts import ADDON_FULL_NAME, SUPPORT_DIR
from ..utils.mime_helper import iter_files
from ..utils.show_options import ImageDimensions
from .common import IS_MAC, IS_WIN, ConverterType, create_process, run_process
from .file_converter import FFmpegNotFoundError, FileConverter, find_ffmpeg_exe

ANIMATED_OR_VIDEO_FORMATS = frozenset(
    [".apng", ".gif", ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg"]
)
AVIF_WORST_CRF = 63


class CanceledPaste(Warning):
    pass


class MimeImageNotFound(Warning):
    pass


@functools.cache
def support_exe_suffix() -> str:
    """
    The mecab executable file in the "support" dir has a different suffix depending on the platform.
    """
    if IS_WIN:
        return ".exe"
    elif IS_MAC:
        return ".mac"
    else:
        return ".lin"


def get_bundled_executable(name: str) -> str:
    """
    Get path to executable in the bundled "support" folder.
    Used to provide "cwebp' and 'ffmpeg' on computers where it is not installed system-wide or can't be found.
    """
    path_to_exe = os.path.join(SUPPORT_DIR, name) + support_exe_suffix()
    assert os.path.isfile(path_to_exe), f"{path_to_exe} doesn't exist. Can't recover."
    if not IS_WIN:
        os.chmod(path_to_exe, 0o755)
    return path_to_exe


@functools.cache
def find_cwebp_exe() -> str:
    # https://developers.google.com/speed/webp/download
    return find_executable_ajt("cwebp") or get_bundled_executable("cwebp")


def fetch_filename(mime: QMimeData) -> Optional[str]:
    for file in iter_files(mime):
        if base := os.path.basename(file):
            return base
    return None


def quality_percent_to_avif_crf(q: int) -> int:
    # https://github.com/strukturag/libheif/commit/7caa01dd150b6c96f33d35bff2eab8a32b8edf2b
    return (100 - q) * AVIF_WORST_CRF // 100


def is_animation(source_path: str) -> bool:
    return get_file_extension(source_path) in ANIMATED_OR_VIDEO_FORMATS


def ffmpeg_not_found_dialog(parent=None):
    return showWarning(
        title=ADDON_FULL_NAME,
        parent=parent,
        text="""
        <h2>FFmpeg is not found in PATH.</h2>

        Install ffmpeg if it is not installed yet.
        Follow <a href="https://wiki.archlinux.org/title/FFmpeg">Arch Wiki</a>
        or the <a href="https://www.ffmpeg.org/">project home page</a> for details.

        Make sure that ffmpeg is added to the PATH.
        To learn how, read
        <a href="https://wiki.archlinux.org/title/Environment_variables#Per_user">this section</a>
        in Arch Wiki or follow your operating system's instructions.
        """,
        textFormat="rich",
    )


def find_image_dimensions(file_path: str) -> ImageDimensions:
    with open(file_path, "rb") as f:
        image = QImage.fromData(f.read())  # type: ignore
    return ImageDimensions(image.width(), image.height())


class ImageConverter(FileConverter, mode=ConverterType.image):
    _source_path: str
    _dimensions: ImageDimensions
    _destination_path: str
    _config: MediaConverterConfig

    def __init__(self, source_path: str, destination_path: str) -> None:
        self._config = get_global_config()
        self._source_path = source_path
        self._destination_path = destination_path
        self._dimensions = find_image_dimensions(source_path)

    @property
    def initial_dimensions(self) -> ImageDimensions:
        return self._dimensions

    def smaller_than_requested(self, image: ImageDimensions) -> bool:
        return 0 < image.width < self._config.image_width or 0 < image.height < self._config.image_height

    def _get_resize_dimensions(self) -> Optional[ImageDimensions]:
        if self._config.avoid_upscaling and self.smaller_than_requested(self._dimensions):
            # skip resizing if the image is already smaller than the requested size
            return None

        if self._config.image_width == 0 and self._config.image_height == 0:
            # skip resizing if both width and height are set to 0
            return None

        # For cwebp, the resize arguments are directly "-resize width height"
        # For ffmpeg, the resize argument is part of the filtergraph: "scale=width:height"
        # The distinction will be made in the respective conversion functions
        return ImageDimensions(self._config.image_width, self._config.image_height)

    def _get_ffmpeg_scale_arg(self) -> str:
        # Check if either width or height is 0 and adjust accordingly
        if resize_args := self._get_resize_dimensions():
            if resize_args.width < 1 and resize_args.height > 0:
                return f"scale=-2:{resize_args.height}"
            elif resize_args.height < 1 and resize_args.width > 0:
                return f"scale={resize_args.width}:-2"
            elif resize_args.width > 0 and resize_args.height > 0:
                return f"scale={resize_args.width}:{resize_args.height}"
        return "scale=-1:-1"

    def _make_to_webp_args(self, source_path: str, destination_path: str) -> list[Union[str, int]]:
        args = [
            find_cwebp_exe(),
            source_path,
            "-o",
            destination_path,
            "-q",
            self._config.image_quality,
            *self._config.cwebp_args,
        ]
        if resize_args := self._get_resize_dimensions():
            args.extend(["-resize", resize_args.width, resize_args.height])
        return args

    def _make_to_avif_args(self, source_path: str, destination_path: str) -> list[Union[str, int]]:
        if not find_ffmpeg_exe():
            raise FFmpegNotFoundError("ffmpeg executable is not in PATH")
        # Use ffmpeg for non-webp formats, dynamically using the format from config
        args = [
            find_ffmpeg_exe(),
            "-hide_banner",
            "-nostdin",
            "-y",
            "-loglevel",
            "quiet",
            "-sn",
            "-an",
            "-i",
            source_path,
            "-c:v",
            "libaom-av1",
            "-vf",
            self._get_ffmpeg_scale_arg() + ":flags=sinc+accurate_rnd",
            "-crf",
            quality_percent_to_avif_crf(self._config.image_quality),
            *self._config.ffmpeg_args,
        ]
        if not is_animation(source_path):
            args += [
                "-still-picture",
                "1",
                "-frames:v",
                "1",
            ]
        args.append(destination_path)
        return args

    def convert(self) -> None:
        if self._config.image_format == ImageFormat.webp:
            args = self._make_to_webp_args(self._source_path, self._destination_path)
        else:
            args = self._make_to_avif_args(self._source_path, self._destination_path)

        print(f"executing args: {args}")
        p = create_process(args)
        run_process(p)

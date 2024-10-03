# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import functools
from typing import Optional

from aqt.qt import *
from aqt.utils import showWarning

from .common import IS_MAC, IS_WIN, ImageDimensions, create_process
from ..ajt_common.utils import find_executable as find_executable_ajt
from ..common import get_file_extension
from ..config import ImageFormat, config
from ..consts import ADDON_FULL_NAME, SUPPORT_DIR
from ..utils.mime_helper import iter_files

ANIMATED_OR_VIDEO_FORMATS = frozenset(
    [".apng", ".gif", ".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg"]
)
AVIF_WORST_CRF = 63


class CanceledPaste(Warning):
    pass


class InvalidInput(Warning):
    pass


class ImageNotLoaded(Exception):
    pass


class FFmpegNotFoundError(FileNotFoundError):
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
def find_ffmpeg_exe() -> Optional[str]:
    # https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
    return find_executable_ajt("ffmpeg")


@functools.cache
def find_cwebp_exe() -> str:
    # https://developers.google.com/speed/webp/download
    return find_executable_ajt("cwebp") or get_bundled_executable("cwebp")


def smaller_than_requested(image: ImageDimensions) -> bool:
    return 0 < image.width < config["image_width"] or 0 < image.height < config["image_height"]


def fetch_filename(mime: QMimeData) -> Optional[str]:
    for file in iter_files(mime):
        if base := os.path.basename(file):
            return base
    return None


def quality_percent_to_avif_crf(q: int) -> int:
    # https://github.com/strukturag/libheif/commit/7caa01dd150b6c96f33d35bff2eab8a32b8edf2b
    return (100 - q) * AVIF_WORST_CRF // 100


def is_animation(source_path: str) -> bool:
    return os.path.splitext(source_path)[1].lower() in ANIMATED_OR_VIDEO_FORMATS


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


class ImageConverter:
    _dimensions: ImageDimensions

    def __init__(self, dimensions: ImageDimensions) -> None:
        self._dimensions = dimensions

    def _get_resize_dimensions(self) -> Optional[ImageDimensions]:
        if config["avoid_upscaling"] and smaller_than_requested(self._dimensions):
            # skip resizing if the image is already smaller than the requested size
            return None

        if config["image_width"] == 0 and config["image_height"] == 0:
            # skip resizing if both width and height are set to 0
            return None

        # For cwebp, the resize arguments are directly "-resize width height"
        # For ffmpeg, the resize argument is part of the filtergraph: "scale=width:height"
        # The distinction will be made in the respective conversion functions
        return ImageDimensions(config["image_width"], config["image_height"])

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
            config.image_quality,
            *config["cwebp_args"],
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
            quality_percent_to_avif_crf(config.image_quality),
            *config["ffmpeg_args"],
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

    def convert_image(self, source_path: str, destination_path: str) -> None:
        if config.image_format == ImageFormat.webp:
            args = self._make_to_webp_args(source_path, destination_path)
        else:
            args = self._make_to_avif_args(source_path, destination_path)

        print(f"executing args: {args}")
        p = create_process(args)
        stdout, stderr = p.communicate()

        if p.wait() != 0:
            print("Conversion failed.")
            print(f"exit code = {p.returncode}")
            print(stdout)
            raise RuntimeError(f"Conversion failed with code {p.returncode}.")

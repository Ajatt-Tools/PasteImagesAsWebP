# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from ..config import MediaConverterConfig
from .common import ConverterType, create_process, run_process
from .file_converter import FFmpegNotFoundError, FileConverter, find_ffmpeg_exe


class AudioConverter(FileConverter, mode=ConverterType.audio):
    _source_path: str
    _destination_path: str
    _config: MediaConverterConfig

    def __init__(self, source_path: str, destination_path: str, config: MediaConverterConfig) -> None:
        self._config = config
        self._source_path = source_path
        self._destination_path = destination_path

    def convert(self) -> None:
        if not find_ffmpeg_exe():
            raise FFmpegNotFoundError("ffmpeg executable is not in PATH")

        args = [
            find_ffmpeg_exe(),
            "-hide_banner",
            "-nostdin",
            "-y",
            "-loglevel",
            "quiet",
            "-sn",
            "-vn",
            "-i",
            self._source_path,
            "-c:a",
            "libopus",
            "-vbr",
            "on",
            "-compression_level",
            "10",
            "-map",
            "0:a",
            "-application",
            "audio",
            "-b:a",
            f"{self._config.audio_bitrate_k}k",
            *self._config.ffmpeg_audio_args,
            self._destination_path,
        ]

        print(f"executing args: {args}")
        p = create_process(args)
        run_process(p)

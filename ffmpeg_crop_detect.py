"""Module for detecting video resolution and crop using ffmpeg"""

import re
import subprocess
from pathlib import Path, PurePath


class MediaParser:
    """Class for detecting video resolution and crop"""

    def __init__(self, file=None):
        if file:
            self.__path = Path.absolute(Path(file)).parent
            self.__file = PurePath(file).name
        else:
            self.__file = None
            self.__path = None
        self.__bar_size = None
        self.__res_x = None
        self.__res_y = None

    def set_file_path(self, file):
        """Set absolute file path and file basename"""
        self.__path = Path.absolute(Path(file)).parent
        self.__file = PurePath(file).name

    def get_file_path(self):
        """Returns absolute path"""
        return f"{self.__path}/{self.__file}"

    def get_file(self):
        """Returns file basename"""
        return self.__file

    def get_path(self):
        """Returns path to directory where the file is located"""
        return self.__path

    def get_bar_size(self):
        """Returns bottom (black) bar size"""
        return self.__bar_size

    def set_bar_size(self, bar_size):
        """Sets bottom (black) bar size"""
        self.__bar_size = bar_size

    def get_res_x(self):
        """Returns horizontal resolution"""
        return self.__res_x

    def set_res_x(self, res_x):
        """Sets horizontal resolution"""
        self.__res_x = res_x

    def get_res_y(self):
        """Returns vertical resolution"""
        return self.__res_y

    def set_res_y(self, res_y):
        """Sets vertical resolution"""
        self.__res_y = res_y

    def is_processed(self):
        """Returns boolean if file is already processed"""
        if self.__res_x or self.__res_y or self.__bar_size:
            return True
        else:
            return False

    def crop_info(self):
        """Get vertical video resolution and cropping information using 'ffmpeg
        cropdetect' and horizontal resolution using 'ffprobe'

        Returns None if successful, str error message otherwise"""
        # TODO: if resx is too different from ffprobe value,
        #   use different position: ffmpeg -ss 1200 vs ffmpeg -ss 300
        #   (cropdetect crop=resx:resy:0:bar vs ffprobe res_x)
        if not self.is_processed():
            ## FFmpeg
            cmd_ffmpeg = [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-ss",
                "1200",
                "-i",
                f"{self.get_file_path()}",
                "-vframes",
                "60",
                "-vf",
                "cropdetect",
                "-f",
                "null",
                "-",
            ]
            proc = subprocess.Popen(
                cmd_ffmpeg,
                bufsize=0,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            # check=False
            cmd_output = proc.stdout.read()  # type: ignore
            proc.stdout.flush()  # type: ignore
            pattern = re.compile(r"^.*crop=\d+:(\d+):.*:(\d+)$", re.MULTILINE)
            list_crop_info = pattern.findall(cmd_output)
            result_crop_info = list_crop_info[-1]
            # FFProbe
            cmd_ffprobe = [
                "ffprobe",
                "-hide_banner",
                "-v",
                "error",
                "-select_streams",
                "0",
                "-show_entries",
                "stream=width",
                "-of",
                "csv=p=0",
                f"{self.get_file_path()}",
            ]
            proc = subprocess.Popen(
                cmd_ffprobe,
                bufsize=0,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            )
            cmd_ffprobe_output = proc.stdout.read()  # type: ignore
            proc.stdout.flush()  # type: ignore
            res_x = cmd_ffprobe_output.strip()
            res_x = re.sub(r"\D", "", res_x)
            try:
                self.__res_x = int(res_x)
                self.__res_y = (
                    f"{int(re.sub(r"\D", "", result_crop_info[0])) + 2 * int(re.sub(r"\D", "", result_crop_info[1]))}"
                )
                self.__bar_size = int(re.sub(r"\D", "", result_crop_info[1]))
                return None
            except AttributeError as ex:
                return f"Error parsing cropping information: {ex}"
        else:
            return None

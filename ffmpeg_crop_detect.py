"""Module for detecting video resolution and crop using ffmpeg"""

import os
import re
import subprocess


class GetMediaInformation:
    """Class for detecting video resolution and crop"""

    def __init__(self):
        self.__file = None
        self.__path = None
        self.__bar_size = None
        self.__res_x = None
        self.__res_y = None

    def set_file_path(self, file):
        """Set absolute file path and file basename"""
        self.__path = os.path.dirname(os.path.abspath(file))
        self.__file = os.path.basename(file)

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

    def get_res_x(self):
        """Returns horizontal resolution"""
        return self.__res_x

    def get_res_y(self):
        """Returns vertical resolution"""
        return self.__res_y

    def crop_info(self):
        """Get vertical video resolution and cropping information using 'ffmpeg
        cropdetect' and horizontal resolution using 'ffprobe'

        Returns None if successful, str error message otherwise"""
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

        cmd_output = proc.stdout.read() # type: ignore
        proc.stdout.flush() # type: ignore

        pattern = re.compile(r"^.*crop=\d+:(\d+):.*:(\d+)$", re.MULTILINE)
        list_crop_info = pattern.findall(cmd_output)
        result_crop_info = list_crop_info[-1]

        # ffprobe
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
            f"{self.get_file_path()}"
        ]

        proc = subprocess.Popen(
            cmd_ffprobe,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )

        cmd_ffprobe_output = proc.stdout.read() # type: ignore
        proc.stdout.flush() # type: ignore
        res_x = cmd_ffprobe_output.strip()

        try:
            self.__res_x = int(res_x)
            self.__res_y = (
                f"{int(result_crop_info[0]) + 2 * int(result_crop_info[1])}"
            )
            self.__bar_size = result_crop_info[1]
            return None
        except AttributeError as ex:
            return f"Error parsing cropping information: {ex}"

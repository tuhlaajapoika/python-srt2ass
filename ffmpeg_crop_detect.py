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
        """Get video resolution and cropping information from ffmpeg
        cropdetect output for eg. crop=3840:1600:0:280

        Returns None if successful, str error message otherwise"""
        #  2>&1 | \
        #   tail -3 | \
        #   sed -n -e 's/^.* crop=\([0-9:]*\)$/\1/ p'
        # ->
        cmd = [
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-ss",
            "30",
            "-t",
            "5",
            "-i",
            f"{self.get_file_path()}",
            "-vframes",
            "10",
            "-vf",
            "cropdetect",
            "-f",
            "null",
            "-",
        ]

        proc = subprocess.Popen(
            cmd,
            bufsize=0,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        # check=False

        cmd_output = proc.stdout.read()
        proc.stdout.flush()

        pattern = re.compile(r"^.*crop=(\d+):(\d+):.*:(\d+)$", re.MULTILINE)
        result_crop_info = pattern.search(cmd_output)

        try:
            self.__bar_size = result_crop_info.group(3)
            self.__res_x = result_crop_info.group(1)
            self.__res_y = (
                f"{int(result_crop_info.group(2)) + 2 * int(self.__bar_size)}"
            )
            return None
        except AttributeError as ex:
            return f"Error parsing cropping information: {ex}"

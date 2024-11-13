#!/usr/bin/env python
"""Module for converting subtitle format .srt to .ass"""

# -*- coding: utf-8 -*-
#
# python-srt2ass: https://github.com/ewwink/python-srt2ass
# by: ewwink
#
# forked: tuhlaajapoika

import argparse
import re
import sys
import codecs
import time
import ffmpeg_crop_detect as ff
from pathlib import Path, PurePath


SCALING_FACTOR = 3.75
IS_SILENT = False
USE_BOX = False


def file_open(input_file):
    encodings = ["utf-32", "utf-16", "utf-8", "cp1252", "gb2312", "gbk", "big5"]
    tmp = ""
    for enc in encodings:
        try:
            with codecs.open(input_file, mode="r", encoding=enc) as fd:
                tmp = fd.read()
                break
        except UnicodeError:
            # print(f"{enc} failed", file=sys.stderr)
            continue
    return [tmp, enc]


def get_header(
    ffmpeg_detect, video_heigth, video_width, sub_position, sub_size, is_hdr
):
    if sub_position is None:  # Default subtitle position
        sub_position = 40
    else:
        sub_position = int(re.sub(r"\D", "", str(sub_position)))
    if sub_size is None:  # Default subtitle size
        sub_size = 16
    else:
        sub_size = int(re.sub(r"\D", "", str(sub_size)))

    ffmpeg_result = None
    # If res hasn't been set by user, try to parse values from media
    if not video_heigth or not video_width:
        ffmpeg_result = ffmpeg_detect.crop_info()
    else:
        # TODO: if not set
        ffmpeg_detect.set_res_y(video_heigth)
        ffmpeg_detect.set_res_x(video_width)
        ffmpeg_detect.set_bar_size("0")

    if ffmpeg_result is None:
        bar_size = int(ffmpeg_detect.get_bar_size())
        res_x = int(ffmpeg_detect.get_res_x())
        res_y = int(ffmpeg_detect.get_res_y())
        play_res_x = ""
        play_res_y = ""

        margin_vertical = int(sub_position)
        outline_size = 1.6
        scaled_sub_size = sub_size

        if res_x > 1900:
            play_res_x = f"PlayResX: {res_x}"
            play_res_y = f"PlayResY: {res_y}"
            margin_vertical = margin_vertical + bar_size
            outline_size = outline_size * 2
            scaled_sub_size = sub_size * SCALING_FACTOR
            if res_x > 3000:
                outline_size = outline_size * 2
                scaled_sub_size = sub_size * 2 * SCALING_FACTOR
        shadow_size = outline_size

        if is_hdr:
            primary_colour = "&H00646464"
        else:
            primary_colour = "&H33DCF0FA"

        if USE_BOX:
            border_style = 3
        else:
            border_style = 1

        secondary_colour = "&H0000FFFF"
        outline_colour = "&H00000000"
        back_colour = "&H02000000"

        return f"""[Script Info]
; This is an Advanced Sub Station Alpha v4+ script.
Title:
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
ScaledBorderAndShadow: Yes
{play_res_x}
{play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{scaled_sub_size},{primary_colour},{secondary_colour},{outline_colour},{back_colour},0,0,0,0,100,100,0,0,{border_style},{outline_size},{shadow_size},2,10,10,{margin_vertical},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

    else:
        print("ERROR")
        print(ffmpeg_result, file=sys.stderr)
        exit(1)


def srt2ass(
    ffmpeg_detect,
    input_file,
    video_heigth,
    video_width,
    sub_position,
    sub_size,
):

    if ".ass" in input_file:
        return input_file

    if not Path(input_file).is_file:
        print(f"    {input_file} does not exist")
        return

    src = file_open(input_file)
    tmp = src[0]
    encoding = src[1]
    src = ""
    utf8bom = ""

    if "\ufeff" in tmp:
        tmp = tmp.replace("\ufeff", "")
        utf8bom = "\ufeff"
    tmp = tmp.replace("\r", "")
    tmp = tmp.replace("...", "\u2026")
    lines = [x.strip() for x in tmp.split("\n") if x.strip()]
    sub_lines = ""
    tmp_lines = ""
    line_count = 0
    output_file = ".".join(input_file.split(".")[:-1])
    output_file += ".ass"

    for ln in range(len(lines)):
        line = lines[ln]
        if line.isdigit() and re.match(r"-?\d\d:\d\d:\d\d", lines[(ln + 1)]):
            if tmp_lines:
                sub_lines += tmp_lines + "\n"
            tmp_lines = ""
            line_count = 0
            continue
        else:
            if re.match(r"-?\d\d:\d\d:\d\d", line):
                line = line.replace("-0", "0")
                tmp_lines += "Dialogue: 0," + line + ",Default,,0,0,0,,"
            else:
                if line_count < 2:
                    tmp_lines += line
                else:
                    tmp_lines += "\\N" + line
            line_count += 1
        ln += 1

    sub_lines += tmp_lines + "\n"

    sub_lines = re.sub(r"\d(\d:\d{2}:\d{2}),(\d{2})\d", "\\1.\\2", sub_lines)
    sub_lines = re.sub(r"\s+-->\s+", ",", sub_lines)
    # replace style
    sub_lines = re.sub(r"<([ubi])>", r"{\\\g<1>1}", sub_lines)
    sub_lines = re.sub(r"</([ubi])>", r"{\\\g<1>0}", sub_lines)
    sub_lines = re.sub(
        r'<font\s+color="?#(\w{2})(\w{2})(\w{2})"?>',
        "{\\\\c&H\\3\\2\\1&}",
        sub_lines,
    )
    sub_lines = re.sub(r"</font>", "", sub_lines)

    # TODO: Use FFmpeg to get HDR metadata
    is_hdr = bool(
        re.search(
            r"(HDR|DV|DolbyVision|Dolby\.Vision|Dolby Vision)", input_file
        )
    )

    head_str = get_header(
        ffmpeg_detect, video_heigth, video_width, sub_position, sub_size, is_hdr
    )

    output_str = utf8bom + head_str + "\n" + sub_lines
    output_str = output_str.encode(encoding)

    with open(output_file, "wb") as output:
        output.write(output_str)

    output_file = output_file.replace("\\", "\\\\")
    output_file = output_file.replace("/", "//")
    return output_file


def get_mediafile_format(file_path_no_suffix):
    """Tests if file is found with a certain suffix.
    @params:
        file_path_no_suffix - Required : file path without file extension
    @return: str    file extension or empty if not found"""
    video_formats = ["avi", "mkv", "mov", "mp4", "mpjpeg", "webm"]
    for suffix in video_formats:
        media_file = Path(f"{file_path_no_suffix}.{suffix}")
        if media_file.is_file():
            return suffix
    return ""


# TODO: Scan filesystem for media files and add proper handling if none is found
def parse_file_name(input_file):
    """Replaces subtitle suffix with video file extension while.
    Removes subtitle naming flags in the process:
        filename.default.eng.sdh.forced.srt to filename.mkv
    @params:
        file_path_no_suffix - Required : file path without file extension
    @return:
        str - absolute path to media file"""
    directory = Path.absolute(Path(input_file)).parent
    # regex rule for filename.default.eng.sdh.forced.srt:
    # ^(.*?)((?:\.default|\.forced)*(?:\.[a-z]{2,3}){0,2}(?:\.default|\.forced)*)(\.srt)$
    pattern = re.compile(
        r"^(.*?)((?:\.default|\.forced)*(?:\.[a-z]{2,3}){0,2}(?:\.default|\.forced)*)(\.srt)$"
    )
    file_name_re = pattern.search(PurePath(input_file).name)  # basename
    file_path_no_suffix = f"{directory}/{file_name_re.group(1)}"  # type: ignore
    suffix = get_mediafile_format(file_path_no_suffix)
    return f"{file_path_no_suffix}.{suffix}"


def progress_bar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=100,
    fill="█",
    printend="\r",
):
    """Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(
        100 * (iteration / float(total))
    )
    filledlength = int(length * iteration // total)
    bar = fill * filledlength + "-" * (length - filledlength)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=printend)
    # Print New Line on Complete
    if iteration == total:
        print()


# TODO: srt2ass as a module and separate rest
def main(arguments):
    err_subs_list = []
    err_media_list = []
    media_file = ""
    ffmpeg_detect = ff.MediaParser()
    sorted_list = sorted(arguments.input_list)
    ls_length = len(sorted_list)
    if not IS_SILENT:
        progress_bar(0, ls_length, prefix="Progress:", suffix="Complete", length=50)
    # for file in progress_bar(sorted_list, l, "Progress:", "Complete", 1, 50, s):
    #   do stuff
    # time.sleep(0.1)
    for i, file in enumerate(sorted_list):
        if not Path(file).is_file():
            # Unable to read subs file
            err_subs_list.append(f"{file}")
            continue
        media_file_new = parse_file_name(file)
        if not Path(media_file_new).is_file():
            # Unable to find corresponding media file for input subs file
            err_media_list.append(f"{media_file_new}")
            continue
        # Test if we're processing multiple subs for the same media
        if media_file != media_file_new:
            media_file = media_file_new
            ffmpeg_detect = ff.MediaParser(media_file)
            # ffmpeg_detect.set_file_path(media_file)
        srt2ass(
            ffmpeg_detect,
            file,
            arguments.video_heigth,
            arguments.video_width,
            arguments.position,
            arguments.size,
        )
        if not IS_SILENT:
            time.sleep(0.1)
            progress_bar(
                i + 1, ls_length, prefix="Progress:", suffix="Complete", length=50
            )
    if len(err_subs_list) > 0:
        print("\n\nCould not read files:\n")
        for i in range(len(err_subs_list)):
            print(f"{err_subs_list[i]}")
    if len(err_media_list) > 0:
        print("\n\nCouldn't find media files:\n")
        for i in range(len(err_media_list)):
            # file = err_media_list[i]
            file = re.sub(r"\.$", "", err_media_list[i])
            print(f"{file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts subs from SubRip to Advanced Sub Station Alpha"
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        type=str,
        dest="input_list",
        help="input file(s)",
        required=True,
    )
    parser.add_argument(
        "-b",
        "--box",
        action="store_true",
        help="use opaque box for subs",
        required=False,
    )
    parser.add_argument(
        "-p",
        "--position",
        help="set subtitle position from the bottom, defaults to [24] px",
        required=False,
    )
    parser.add_argument(
        "-x",
        "--width",
        help="override video width, skips ffprobe",
        type=int,
        dest="video_width",
        required=False,
    )
    parser.add_argument(
        "-y",
        "--heigth",
        help="override video heigth, skips ffprobe",
        type=int,
        dest="video_heigth",
        required=False,
    )
    parser.add_argument(
        "-sz",
        "--size",
        help="set subtitle size, defaults to [16]",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--silent",
        action="store_true",
        help="don't print output",
        required=False,
    )
    parser.add_argument(  # TODO: verbose
        "-v",
        "--verbose",
        action="store_true",
        help="verbose output",
        required=False,
    )
    args = parser.parse_args()
    IS_SILENT = args.silent
    USE_BOX = args.box
    # args._get_kwargs()
    main(args)

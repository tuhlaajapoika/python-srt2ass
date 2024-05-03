"""Module for converting subtitles from SubRip to ASS"""

# -*- coding: utf-8 -*-
#
# python-srt2ass: https://github.com/ewwink/python-srt2ass
# by: ewwink
#

import argparse
import os
import re
import sys
import codecs
import ffmpeg_crop_detect as ff
from pathlib import Path


SCALING_FACTOR = 3.75


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


def get_header(ffmpeg_detect, sub_offset, sub_size, is_hdr):
    ffmpeg_result = ffmpeg_detect.crop_info()
    if ffmpeg_result is None:
        bar_size = int(ffmpeg_detect.get_bar_size())
        res_x = int(ffmpeg_detect.get_res_x())
        res_y = int(ffmpeg_detect.get_res_y())
        play_res_x = ""
        play_res_y = ""

        sub_margin = sub_offset
        sub_border_outline = 1.6
        scaled_sub_size = sub_size

        if res_y >= 1080:
            play_res_x = f"PlayResX: {res_x}"
            play_res_y = f"PlayResY: {res_y}"
            sub_margin = sub_margin + bar_size
            sub_border_outline = sub_border_outline * 2
            scaled_sub_size = sub_size * SCALING_FACTOR
            if res_y >= 2160:
                sub_border_outline = sub_border_outline * 2
                scaled_sub_size = sub_size * 2 * SCALING_FACTOR
        sub_border_shadow = sub_border_outline

        if is_hdr:
            font_color = "&H00646464"
        else:
            font_color = "&H33DCF0FA"

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
Style: Default,Arial,{scaled_sub_size},{font_color},&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,{sub_border_outline},{sub_border_shadow},2,10,10,{sub_margin},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

    else:
        print("ERROR")
        print(ffmpeg_result, file=sys.stderr)
        exit(1)


def srt2ass(input_file, sub_offset, sub_size, ffmpeg_detect):
    # Default subtitle offset/position
    if sub_offset is None:
        sub_offset = 24

    # Default subtitle size
    if sub_size is None:
        sub_size = 16

    if ".ass" in input_file:
        return input_file

    if not os.path.isfile(input_file):
        print(f"{input_file} does not exist")
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
    sub_lines = re.sub("<([ubi])>", r"{\\\\\g<1>1}", sub_lines)
    sub_lines = re.sub("</([ubi])>", r"{\\\\\g<1>0}", sub_lines)
    sub_lines = re.sub(
        r'<font\s+color="?#(\w{2})(\w{2})(\w{2})"?>',
        r"{\\\\c&H\\3\\2\\1&}",
        sub_lines,
    )
    sub_lines = re.sub("</font>", "", sub_lines)

    # TODO: Use FFmpeg to get HDR metadata
    is_hdr = bool(
        re.search(
            r"(HDR|DV|DolbyVision|Dolby\.Vision|Dolby Vision)", input_file
        )
    )

    head_str = get_header(ffmpeg_detect, sub_offset, sub_size, is_hdr)

    output_str = utf8bom + head_str + "\n" + sub_lines
    output_str = output_str.encode(encoding)

    with open(output_file, "wb") as output:
        output.write(output_str)

    output_file = output_file.replace("\\", "\\\\")
    output_file = output_file.replace("/", "//")
    return output_file


def parse_file_name(file):
    """Replaces .srt or en.srt or eng.srt suffix with .mkv

    Returns: absolute path to media file as str"""
    path = os.path.dirname(os.path.abspath(file))
    suffix_re = re.search(r"(\.[a-z]{2,3}\.srt|\.srt)$", file)
    file_base_name = (
        os.path.basename(file).removesuffix(suffix_re.group()) + ".mkv"
    )
    return f"{path}/{file_base_name}"


def main(args):
    ffmpeg_detect = ff.GetMediaInformation()
    media_file = ""
    sorted_list = sorted(args.input_list)
    for file in sorted_list:
        if not Path(file).is_file():
            print(f"Could not read file: {file}")
            exit(1)
        # TODO: Scan filesystem for media files and add proper
        #       handling if none is found
        file_name = parse_file_name(file)
        if file_name != media_file:
            media_file = file_name
            ffmpeg_detect.set_file_path(media_file)
        srt2ass(file, args.offset, args.size, ffmpeg_detect)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert subtitles from SubRip (SRT) to Advanced Sub Station Alpha (ASS)"
    )
    parser.add_argument(
        "-i",
        "--input",
        nargs="+",
        type=str,
        dest="input_list",
        help="File name",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--offset",
        help="Set subtitle offset from the bottom, defaults to 24 px",
        required=False,
    )
    parser.add_argument(
        "-s",
        "--size",
        help="Set subtitle size, defaults to 16",
        required=False,
    )
    arguments = parser.parse_args()
    main(arguments)

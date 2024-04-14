# -*- coding: utf-8 -*-
#
# python-srt2ass: https://github.com/ewwink/python-srt2ass
# by: ewwink
#

import sys
import os
import re
import codecs


def fileopen(input_file):
    encodings = ["utf-32", "utf-16", "utf-8", "cp1252", "gb2312", "gbk", "big5"]
    tmp = ""
    for enc in encodings:
        try:
            with codecs.open(input_file, mode="r", encoding=enc) as fd:
                tmp = fd.read()
                break
        except:
            # print enc + ' failed'
            continue
    return [tmp, enc]


def srt2ass(input_file):
    if ".ass" in input_file:
        return input_file

    if not os.path.isfile(input_file):
        print(input_file + " not exist")
        return

    src = fileopen(input_file)
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
        if line.isdigit() and re.match("-?\d\d:\d\d:\d\d", lines[(ln + 1)]):
            if tmp_lines:
                sub_lines += tmp_lines + "\n"
            tmp_lines = ""
            line_count = 0
            continue
        else:
            if re.match("-?\d\d:\d\d:\d\d", line):
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
    sub_lines = re.sub(r"<([ubi])>", "{\\\\\g<1>1}", sub_lines)
    sub_lines = re.sub(r"</([ubi])>", "{\\\\\g<1>0}", sub_lines)
    sub_lines = re.sub(
        r'<font\s+color="?#(\w{2})(\w{2})(\w{2})"?>',
        "{\\\\c&H\\3\\2\\1&}",
        sub_lines,
    )
    sub_lines = re.sub(r"</font>", "", sub_lines)

    is_hdr = bool(
        re.search(
            r"(HDR|DV|DolbyVision|Dolby\.Vision|Dolby Vision)", input_file
        )
    )
    if is_hdr:
        head_str = """[Script Info]
; This is an Advanced Sub Station Alpha v4+ script.
Title:
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
ScaledBorderAndShadow: Yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,16,&H00646464,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1.4,1.4,2,10,10,24,1

[Events]
Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text"""
    else:
        head_str = """[Script Info]
; This is an Advanced Sub Station Alpha v4+ script.
Title:
ScriptType: v4.00+
Collisions: Normal
PlayDepth: 0
ScaledBorderAndShadow: Yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,16,&H33DCF0FA,&H0000FFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,1.4,1.4,2,10,10,24,1

[Events]
Format: Layer, Start, End, Style, Actor, MarginL, MarginR, MarginV, Effect, Text"""

    output_str = utf8bom + head_str + "\n" + sub_lines
    output_str = output_str.encode(encoding)

    with open(output_file, "wb") as output:
        output.write(output_str)

    output_file = output_file.replace("\\", "\\\\")
    output_file = output_file.replace("/", "//")
    return output_file


if len(sys.argv) > 1:
    for name in sys.argv[1:]:
        srt2ass(name)

# python-srt2ass

Python script to convert subtitle formats from `.srt` to `.ass`.

By default subtitles will use
- warm white colour with sligth transparency for SDR content
- dark gray colour for HDR content
- and black borders/shadow for both.

FFmpeg is used to detect video area resolution and black bars for proper subtitle positioning.

## Requirements

- FFmpeg
- [Python 3](https://www.python.org/downloads/)
- Windows/Linux/Mac/Android

## How to use

```
python srt2ass.py -i "file"
or
python srt2ass.py -i "file" -s 16 -o 40
or
python srt2ass.py --input "file" --size 16 --offset 40
```

## Sample

**Using command line**

```shell
$ python srt2ass.py -i file1.srt
$ python srt2ass.py -i file1.srt file2.srt file3.srt
$ python srt2ass.py -i *.srt -s 20 -o 48
$ python srt2ass.py --input *.srt --size 20 --offset 48
```

**Using as module**

(FIXME)

```python
from srt2ass import srt2ass

assSub = srt2ass("file.srt")
print('ASS subtitle saved as: ' + assSub)
# ASS subtitle saved as: file.ass
```

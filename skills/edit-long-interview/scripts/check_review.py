#!/usr/bin/env python3
"""Check an interview review export and its SubRip subtitle tracks."""

import argparse
import json
import math
import re
import subprocess
from pathlib import Path


TIMESTAMP = r"[0-9]{2,}:[0-5][0-9]:[0-5][0-9][,.][0-9]{3}"
CUE_LINE = re.compile(rf"^({TIMESTAMP})\s*-->\s*({TIMESTAMP})(?:\s+.*)?$")
MILLISECOND_TOLERANCE = 50


def timestamp_ms(value):
    if re.fullmatch(TIMESTAMP, value) is None:
        raise ValueError(f"Invalid timestamp {value!r}. Use HH:MM:SS,mmm.")
    hours, minutes, seconds, milliseconds = map(int, re.split("[:,.]", value))
    return ((hours * 60 + minutes) * 60 + seconds) * 1000 + milliseconds


def display_time(milliseconds):
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, remainder = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{remainder:03d}"


def probe_video(path):
    process = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=codec_type,width,height:stream_disposition=attached_pic",
            "-of", "json", str(path.resolve()),
        ],
        capture_output=True,
        text=True,
    )
    if process.returncode:
        detail = process.stderr.strip() or "ffprobe could not read the file"
        raise ValueError(f"{path.name} could not be probed. {detail}")

    info = json.loads(process.stdout)
    streams = info.get("streams", [])
    pictures = [
        stream for stream in streams
        if stream.get("codec_type") == "video"
        and not stream.get("disposition", {}).get("attached_pic")
    ]
    if not pictures or not any(stream.get("codec_type") == "audio" for stream in streams):
        raise ValueError(f"{path.name} must contain video and audio.")

    try:
        duration = float(info.get("format", {}).get("duration", "nan"))
    except (TypeError, ValueError):
        duration = math.nan
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError(f"{path.name} has no valid duration.")
    video = pictures[0]
    return round(duration * 1000), video.get("width"), video.get("height")


def read_cues(path, limit_ms):
    source = path.read_text(encoding="utf-8-sig").strip()
    if not source:
        raise ValueError(f"{path.name} is empty.")

    cues = []
    for number, block in enumerate(re.split(r"\n[ \t]*\n+", source), start=1):
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].strip().isdigit():
            raise ValueError(f"{path.name} cue {number} needs a cue index and text.")
        match = CUE_LINE.fullmatch(lines[1].strip())
        if not match or not any(line.strip() for line in lines[2:]):
            raise ValueError(f"{path.name} cue {number} has an invalid timing line or empty text.")
        start, end = map(timestamp_ms, match.groups())
        if end <= start or (cues and start < cues[-1][0]):
            raise ValueError(f"{path.name} cue {number} is out of time order.")
        if end > limit_ms + MILLISECOND_TOLERANCE:
            raise ValueError(f"{path.name} cue {number} ends at {display_time(end)}, beyond {display_time(limit_ms)}.")
        cues.append((start, end))
    return cues


def verify_alignment(reference_name, reference, other_name, other):
    if len(reference) != len(other):
        raise ValueError(f"{reference_name} has {len(reference)} cues and {other_name} has {len(other)}.")
    for number, (first, second) in enumerate(zip(reference, other), start=1):
        if first != second:
            first_time = " to ".join(map(display_time, first))
            second_time = " to ".join(map(display_time, second))
            raise ValueError(
                f"Cue {number} differs. {reference_name} uses {first_time}. "
                f"{other_name} uses {second_time}."
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--srt", type=Path, action="append", required=True, help="Subtitle track. Repeat for each language")
    parser.add_argument("--subtitle-end", help="Latest intended dialogue caption as HH:MM:SS,mmm")
    parser.add_argument("--match-cues", action="store_true", help="Require identical timestamps across tracks")
    args = parser.parse_args()
    if args.match_cues and len(args.srt) < 2:
        parser.error("--match-cues requires at least two --srt files")

    try:
        duration, width, height = probe_video(args.video)
        subtitle_end = timestamp_ms(args.subtitle_end) if args.subtitle_end else duration
        if subtitle_end > duration + MILLISECOND_TOLERANCE:
            raise ValueError("The specified subtitle end exceeds the video duration.")
        tracks = [(path, read_cues(path, subtitle_end)) for path in args.srt]
        if args.match_cues:
            first_path, first_cues = tracks[0]
            for other_path, other_cues in tracks[1:]:
                verify_alignment(first_path.name, first_cues, other_path.name, other_cues)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Review check failed. {error}\n")

    print(f"Video {args.video.name} · {width}×{height} · {display_time(duration)} · audio present")
    for path, cues in tracks:
        print(f"{path.name} · {len(cues)} cues · {display_time(cues[0][0])} to {display_time(max(end for _, end in cues))}")
    if args.match_cues:
        print("Cue boundaries match across all subtitle tracks.")
    print(f"Subtitle timing limit {display_time(subtitle_end)}")


if __name__ == "__main__":
    main()

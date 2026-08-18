#!/usr/bin/env python3
"""Render a timed Wenu circumpolar sequence and assemble an MP4 movie."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import struct
import subprocess


DEFAULT_START = "2026-08-21T21:00:00-04:00"
DEFAULT_DURATION_HOURS = 12.0
DEFAULT_MOVIE_SECONDS = 15.0
DEFAULT_FPS = 12


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--start", default=DEFAULT_START)
    value.add_argument("--duration-hours", type=float, default=DEFAULT_DURATION_HOURS)
    value.add_argument("--movie-seconds", type=float, default=DEFAULT_MOVIE_SECONDS)
    value.add_argument("--fps", type=int, default=DEFAULT_FPS)
    value.add_argument(
        "--title",
        default="Constelaciones circumpolares australes",
    )
    value.add_argument("--location-label", default="La Ligua")
    value.add_argument("--background-color", default="#0262AD")
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/circumpolar-south-12h.mp4"),
    )
    value.add_argument(
        "--frames",
        type=Path,
        default=Path("output/circumpolar-south-12h-frames"),
    )
    value.add_argument(
        "--rerender",
        action="store_true",
        help="render frames again even when their PNG files already exist",
    )
    value.add_argument(
        "--time-in-title",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    value.add_argument(
        "wenu_arguments",
        nargs=argparse.REMAINDER,
        help="additional wenu_chart arguments after --",
    )
    return value


def aware_datetime(value: str) -> datetime:
    instant = datetime.fromisoformat(value)
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise SystemExit("--start must include a UTC offset, for example -04:00")
    return instant


def require_program(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        raise SystemExit(f"Required program not found: {name}")
    return executable


def frame_times(start: datetime, duration: timedelta, count: int):
    if count < 2:
        raise SystemExit("The movie requires at least two frames")
    return tuple(start + duration * (index / (count - 1)) for index in range(count))


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"Not a valid PNG frame: {path}")
    return struct.unpack(">II", header[16:24])


def render(arguments: argparse.Namespace) -> Path:
    if arguments.duration_hours <= 0.0:
        raise SystemExit("--duration-hours must be positive")
    if arguments.movie_seconds <= 0.0:
        raise SystemExit("--movie-seconds must be positive")
    if arguments.fps <= 0:
        raise SystemExit("--fps must be positive")

    wenu_chart = require_program("wenu_chart")
    ffmpeg = require_program("ffmpeg")
    start = aware_datetime(arguments.start)
    duration = timedelta(hours=arguments.duration_hours)
    frame_count = round(arguments.movie_seconds * arguments.fps)
    instants = frame_times(start, duration, frame_count)
    extra = list(arguments.wenu_arguments)
    if extra[:1] == ["--"]:
        extra = extra[1:]
    controlled = {"--observer-time", "--output", "--title"}
    conflicts = sorted(controlled & set(extra))
    if conflicts:
        raise SystemExit(
            "Pass movie-controlled options before --, not to wenu_chart: "
            + ", ".join(conflicts)
        )

    arguments.frames.mkdir(parents=True, exist_ok=True)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)

    for index, instant in enumerate(instants):
        destination = arguments.frames / f"frame-{index:04d}.png"
        print(
            f"[{index + 1:03d}/{frame_count:03d}] "
            f"{instant.isoformat()} -> {destination}",
            flush=True,
        )
        if destination.exists() and not arguments.rerender:
            continue
        title = arguments.title
        if arguments.time_in_title:
            title += (
                f" — {arguments.location_label} — "
                f"{instant:%Y-%m-%d %H:%M}"
            )
        command = [
            wenu_chart,
            "circumpolar",
            "--pole", "south",
            "--limiting-declination", "-60",
            "--declination-step", "10",
            "--style", "cartoon",
            "--mode", "presentation",
            "--observer-location", "La Ligua",
            "--observer-time", instant.isoformat(),
            "--constellation-lines",
            "--constellation-line-width", "1.2",
            "--magnitude-limit", "5.0",
            "--language", "es",
            "--title", title,
            "--output", str(destination),
            *extra,
        ]
        subprocess.run(command, check=True)

    width, height = png_size(arguments.frames / "frame-0000.png")
    background = arguments.background_color.replace("#", "0x")
    video_filter = (
        f"color=c={background}:s={width}x{height}:r={arguments.fps}[bg];"
        "[bg][0:v]overlay=shortest=1,"
        "scale=trunc(iw/2)*2:trunc(ih/2)*2"
    )
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate", str(arguments.fps),
            "-i", str(arguments.frames / "frame-%04d.png"),
            "-filter_complex", video_filter,
            "-c:v", "libx264",
            "-preset", "slow",
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(arguments.output),
        ],
        check=True,
    )
    return arguments.output


def main() -> None:
    print(render(parser().parse_args()))


if __name__ == "__main__":
    main()

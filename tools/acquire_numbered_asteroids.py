"""Acquire explicit offline Horizons resources for numbered asteroids."""

from __future__ import annotations

import argparse
from pathlib import Path

from wenu.minor_body_acquisition import acquire_numbered_asteroids


def _number(value):
    text = str(value).strip()
    if not text.isdecimal() or int(text) <= 0:
        raise argparse.ArgumentTypeError(
            "asteroid identifiers must be positive permanent numbers"
        )
    return int(text)


def acquire(numbers, output_directory, *, start="2025-01-01", stop="2030-01-01"):
    """Acquire a new immutable numbered-asteroid collection."""
    return acquire_numbered_asteroids(
        numbers, output_directory, start=start, stop=stop
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("numbers", nargs="+", type=_number)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--stop", default="2030-01-01")
    arguments = parser.parse_args()
    print(acquire(
        arguments.numbers,
        arguments.output_directory,
        start=arguments.start,
        stop=arguments.stop,
    ))


if __name__ == "__main__":
    main()

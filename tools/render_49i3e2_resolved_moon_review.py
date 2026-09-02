"""Render the Milestone 49I.3E.2 resolved-Moon review matrix."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys


OBSERVER = (
    "--observer-location", "La Ligua",
    "--observer-time", "2026-01-19T00:00:00Z",
)
COMMON = (
    *OBSERVER,
    "--magnitude-limit", "5.0",
    "--style", "atlas",
    "--mode", "presentation",
)
VISUAL_MAGNIFICATION = "60"
FAMILIES = {
    "regional": (
        "regional", "--constellations", "Cap",
        "--field-width", "55", "--field-height", "45",
        "--orientation", "zenith-up",
    ),
    "binocular": (
        "binocular", "--ra", "301", "--dec", "-20",
        "--display-name", "Moon review field", "--field-diameter", "45",
    ),
    "circumpolar": (
        "circumpolar", "--pole", "south",
        "--limiting-declination", "-15",
    ),
    "planisphere": ("planisphere",),
    "all-sky": ("all-sky",),
}


@dataclass(frozen=True)
class ReviewEntry:
    """One installed-command review render."""

    name: str
    arguments: tuple[str, ...]
    suffix: str
    proves: str


def _entries(common):
    entries = []
    for family, family_arguments in FAMILIES.items():
        entries.append(ReviewEntry(
            f"{family}-physical",
            (*family_arguments, *common, "--moon"),
            ".png",
            f"{family} accepts physical-scale resolved Moon display",
        ))
        entries.append(ReviewEntry(
            f"{family}-magnified",
            (
                *family_arguments, *common, "--moon",
                "--moon-disk-magnification", VISUAL_MAGNIFICATION,
            ),
            ".png",
            f"{family} shows a large Moon without moving its centre",
        ))
        entries.append(ReviewEntry(
            f"{family}-symbolic",
            (
                *family_arguments, *common, "--moon",
                "--moon-appearance", "symbolic",
            ),
            ".png",
            f"{family} preserves explicit symbolic compatibility",
        ))
    regional = FAMILIES["regional"]
    for suffix in (".pdf", ".svg"):
        entries.append(ReviewEntry(
            f"regional-magnified-{suffix[1:]}",
            (
                *regional, *common, "--moon",
                "--moon-disk-magnification", VISUAL_MAGNIFICATION,
            ),
            suffix,
            f"regional magnified Moon {suffix[1:].upper()} export parity",
        ))
    return tuple(entries)


MATRIX = _entries(COMMON)


def _commit():
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def render_matrix(destination, entries=MATRIX):
    """Render entries in isolated command processes and write a manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    configuration = destination / "review-config.toml"
    configuration.write_text(
        "schema_version = 1\n\n"
        "[detail.content]\n"
        'default_layers = ["stars"]\n'
        'cartoon_layers = ["stars"]\n',
        encoding="utf-8",
    )
    records = []
    for index, entry in enumerate(entries, start=1):
        output = destination / f"{entry.name}{entry.suffix}"
        command = (
            sys.executable, "-m", "wenu.cli.chart",
            *entry.arguments,
            "--config", str(configuration),
            "--output", str(output),
        )
        print(f"[{index}/{len(entries)}] {entry.name}", flush=True)
        subprocess.run(command, check=True)
        records.append({
            **asdict(entry),
            "command": (
                "wenu_chart", *entry.arguments,
                "--config", str(configuration),
                "--output", str(output),
            ),
            "output": str(output),
            "bytes": output.stat().st_size,
            "sha256": sha256(output.read_bytes()).hexdigest(),
        })
    manifest = destination / "manifest.json"
    manifest.write_text(
        json.dumps({
            "source_commit": _commit(),
            "entry_count": len(records),
            "entries": records,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/49i3e2-resolved-moon-review"),
    )
    value.add_argument(
        "--entry",
        action="append",
        choices=tuple(entry.name for entry in MATRIX),
        help="render only this entry; repeat to select several",
    )
    value.add_argument(
        "--list", action="store_true", help="list entries without rendering"
    )
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    entries = (
        MATRIX
        if arguments.entry is None
        else tuple(
            entry for entry in MATRIX if entry.name in arguments.entry
        )
    )
    if arguments.list:
        for entry in entries:
            print(f"{entry.name}: {entry.proves}")
        return 0
    print(render_matrix(arguments.output, entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

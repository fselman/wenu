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
    "--observer-time", "2026-09-16T00:00:00Z",
)
COMMON = (
    *OBSERVER,
    "--style", "atlas",
    "--mode", "presentation",
)
VISUAL_MAGNIFICATION = "8"
MOON_RA = "__MOON_RA__"
MOON_DEC = "__MOON_DEC__"
MOON_ALTITUDE = "__MOON_ALTITUDE__"
MOON_AZIMUTH = "__MOON_AZIMUTH__"
FAMILIES = {
    "regional": (
        "regional", "--constellations", "Sco",
        "--field-width", "55", "--field-height", "45",
        "--center-altitude", MOON_ALTITUDE,
        "--center-azimuth", MOON_AZIMUTH,
        "--orientation", "zenith-up", "--magnitude-limit", "5.0",
    ),
    "binocular": (
        "binocular", "--ra", MOON_RA, "--dec", MOON_DEC,
        "--display-name", "Moon review field", "--field-diameter", "7.5",
        "--magnitude-limit", "11.0",
    ),
    "circumpolar": (
        "circumpolar", "--pole", "south",
        "--limiting-declination", "-15",
        "--magnitude-limit", "5.0",
    ),
    "planisphere": ("planisphere", "--magnitude-limit", "5.0"),
    "all-sky": ("all-sky", "--magnitude-limit", "5.0"),
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


def _moon_centre_arguments():
    """Return exact topocentric review centres from the installed kernel."""
    from wenu.observer import Observer

    with Observer(
        location="La Ligua",
        time="2026-09-16T00:00:00Z",
    ) as observer:
        apparent = observer.skyfield.at(observer.t).observe(
            observer.ephemeris["moon"]
        ).apparent()
        ra, dec, _ = apparent.radec()
        altitude, azimuth, _ = apparent.altaz()
    return {
        MOON_RA: f"{float(ra.hours) * 15.0:.12g}",
        MOON_DEC: f"{float(dec.degrees):.12g}",
        MOON_ALTITUDE: f"{float(altitude.degrees):.12g}",
        MOON_AZIMUTH: f"{float(azimuth.degrees):.12g}",
    }


def _centred_arguments(arguments, centres):
    return tuple(centres.get(value, value) for value in arguments)


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
    centres = _moon_centre_arguments()
    print(
        "Moon centre: "
        f"RA {centres[MOON_RA]} deg; Dec {centres[MOON_DEC]} deg; "
        f"altitude {centres[MOON_ALTITUDE]} deg; "
        f"azimuth {centres[MOON_AZIMUTH]} deg",
        flush=True,
    )
    records = []
    for index, entry in enumerate(entries, start=1):
        output = destination / f"{entry.name}{entry.suffix}"
        arguments = _centred_arguments(entry.arguments, centres)
        command = (
            sys.executable, "-m", "wenu.cli.chart",
            *arguments,
            "--config", str(configuration),
            "--output", str(output),
        )
        print(f"[{index}/{len(entries)}] {entry.name}", flush=True)
        subprocess.run(command, check=True)
        records.append({
            **asdict(entry),
            "command": (
                "wenu_chart", *arguments,
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

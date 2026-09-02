"""Render the Milestone 49I.3E.3 fixed-chart Moon sequence matrix."""

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
    "--observer-time", "2026-09-16T12:00:00Z",
)
COMMON = (
    *OBSERVER,
    "--style", "atlas",
    "--mode", "presentation",
    "--moon-disk-sequence",
    "--disk-sequence-model", "observed",
    "--moon-disk-magnification", "8",
)
LONG_SEQUENCE = (
    "--disk-sequence-start", "2026-09-12T00:00:00Z",
    "--disk-sequence-step", "1d",
    "--disk-sequence-n-steps", "7",
)
SHORT_SEQUENCE = (
    "--disk-sequence-start", "2026-09-16T06:00:00Z",
    "--disk-sequence-step", "2h",
    "--disk-sequence-n-steps", "6",
)
MOON_RA = "__MOON_RA__"
MOON_DEC = "__MOON_DEC__"
MOON_ALTITUDE = "__MOON_ALTITUDE__"
MOON_AZIMUTH = "__MOON_AZIMUTH__"


@dataclass(frozen=True)
class ReviewEntry:
    name: str
    arguments: tuple[str, ...]
    suffix: str
    proves: str


REGIONAL = (
    "regional", "--constellations", "Sgr,Sco,Oph",
    "--field-width", "110", "--field-height", "70",
    "--center-altitude", MOON_ALTITUDE,
    "--center-azimuth", MOON_AZIMUTH,
    "--orientation", "zenith-up",
    "--magnitude-limit", "5.0",
)
BINOCULAR = (
    "binocular", "--ra", MOON_RA, "--dec", MOON_DEC,
    "--display-name", "Observed Moon sequence",
    "--field-diameter", "7.5",
    "--magnitude-limit", "11.0",
)
MATRIX = (
    ReviewEntry(
        "regional-sequence", (*REGIONAL, *COMMON, *LONG_SEQUENCE), ".png",
        "changing Moon path and phase in one fixed regional chart",
    ),
    ReviewEntry(
        "regional-sequence-labels",
        (*REGIONAL, *COMMON, *LONG_SEQUENCE, "--disk-sequence-labels"),
        ".png", "shared date-label policy",
    ),
    ReviewEntry(
        "regional-sequence-pdf", (*REGIONAL, *COMMON, *LONG_SEQUENCE), ".pdf",
        "regional PDF parity",
    ),
    ReviewEntry(
        "regional-sequence-svg", (*REGIONAL, *COMMON, *LONG_SEQUENCE), ".svg",
        "regional semantic SVG parity",
    ),
    ReviewEntry(
        "binocular-sequence",
        (*BINOCULAR, *COMMON, *SHORT_SEQUENCE, "--disk-sequence-labels"),
        ".png", "7.5-degree short-cadence binocular sequence",
    ),
    ReviewEntry(
        "circumpolar-sequence",
        (
            "circumpolar", "--pole", "south",
            "--limiting-declination", "-15", "--magnitude-limit", "5.0",
            *COMMON, *LONG_SEQUENCE,
        ),
        ".png", "circumpolar fixed-chart sequence",
    ),
    ReviewEntry(
        "planisphere-sequence",
        ("planisphere", "--magnitude-limit", "5.0", *COMMON, *LONG_SEQUENCE),
        ".png", "planisphere fixed-chart sequence",
    ),
    ReviewEntry(
        "all-sky-sequence",
        ("all-sky", "--magnitude-limit", "5.0", *COMMON, *LONG_SEQUENCE),
        ".png", "Mollweide fixed-chart sequence",
    ),
)


def _commit():
    return subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _moon_centre_arguments():
    from wenu.observer import Observer

    with Observer(
        location="La Ligua", time="2026-09-16T12:00:00Z"
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


def _centred(arguments, centres):
    return tuple(centres.get(value, value) for value in arguments)


def render_matrix(destination, entries=MATRIX):
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
    records = []
    for index, entry in enumerate(entries, start=1):
        arguments = _centred(entry.arguments, centres)
        output = destination / f"{entry.name}{entry.suffix}"
        command = (
            sys.executable, "-m", "wenu.cli.chart", *arguments,
            "--config", str(configuration), "--output", str(output),
        )
        print(f"[{index}/{len(entries)}] {entry.name}", flush=True)
        subprocess.run(command, check=True)
        records.append({
            **asdict(entry),
            "command": (
                "wenu_chart", *arguments,
                "--config", str(configuration), "--output", str(output),
            ),
            "output": str(output),
            "bytes": output.stat().st_size,
            "sha256": sha256(output.read_bytes()).hexdigest(),
        })
    manifest = destination / "manifest.json"
    manifest.write_text(
        json.dumps({
            "source_commit": _commit(),
            "chart_epoch": "2026-09-16T12:00:00Z",
            "entry_count": len(records),
            "entries": records,
        }, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output", type=Path,
        default=Path("output/49i3e3-observed-moon-sequence-review"),
    )
    value.add_argument(
        "--entry", action="append",
        choices=tuple(entry.name for entry in MATRIX),
    )
    value.add_argument("--list", action="store_true")
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    entries = (
        MATRIX if arguments.entry is None
        else tuple(entry for entry in MATRIX if entry.name in arguments.entry)
    )
    if arguments.list:
        for entry in entries:
            print(f"{entry.name}: {entry.proves}")
        return 0
    print(render_matrix(arguments.output, entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

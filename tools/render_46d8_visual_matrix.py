"""Render the fixed Milestone 46D.8 visual-acceptance matrix."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess
import sys


OBSERVER = (
    "--observer-location", "La Ligua",
    "--observer-time", "2026-08-15 21:00",
)
BINOCULAR_OBSERVER = (
    "--observer-location", "La Ligua",
    "--observer-time", "2026-05-15 22:00",
)


@dataclass(frozen=True)
class MatrixEntry:
    """One deterministic installed-command visual diagnostic."""

    name: str
    arguments: tuple[str, ...]
    proves: str


def _canonical(name, family, subject, magnitude):
    observer = BINOCULAR_OBSERVER if family == "binocular" else OBSERVER
    common = (family, *observer, *subject, "--magnitude-limit", magnitude)
    return (
        MatrixEntry(
            f"canonical-{name}-atlas-print",
            (*common, "--style", "atlas", "--mode", "print"),
            f"{name} canonical atlas-print baseline",
        ),
        MatrixEntry(
            f"canonical-{name}-cartoon-presentation",
            (*common, "--style", "cartoon", "--mode", "presentation"),
            f"{name} cartoon-presentation parity smoke",
        ),
    )


MATRIX = (
    *_canonical("all-sky", "all-sky", (), "5.0"),
    *_canonical("planisphere", "planisphere", (), "5.0"),
    *_canonical(
        "regional-single", "regional", ("--constellations", "Cru"), "5.0"
    ),
    *_canonical(
        "regional-group",
        "regional",
        ("--constellations", "Sgr,Sco,Oph,Ser", "--mask"),
        "5.0",
    ),
    *_canonical(
        "circumpolar",
        "circumpolar",
        ("--pole", "south", "--limiting-declination", "-69.75"),
        "5.0",
    ),
    *_canonical(
        "binocular",
        "binocular",
        ("--target", "centaurus-a", "--field-diameter", "6.5"),
        "11.0",
    ),
    MatrixEntry(
        "diagnostic-all-sky-constellation-mask",
        (
            "all-sky", *OBSERVER, "--constellations", "Cru,Cyg,UMa",
            "--mask",
            "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "three disjoint constellation openings in one outside mask",
    ),
    MatrixEntry(
        "diagnostic-regional-explicit-field-mask",
        (
            "regional", *OBSERVER, "--constellations", "Oph,Ser", "--mask",
            "--field-width", "80", "--field-height", "50",
            "--position-angle", "12.5",
            "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "explicit regional field and one combined Ophiuchus/Serpens mask",
    ),
    MatrixEntry(
        "diagnostic-binocular-field",
        (
            "binocular", *BINOCULAR_OBSERVER, "--target", "centaurus-a",
            "--field-diameter", "6.5",
            "--magnitude-limit", "11.0",
            "--style", "atlas", "--mode", "print",
        ),
        "binocular aperture, target content, and family furniture",
    ),
    MatrixEntry(
        "diagnostic-circumpolar-horizon",
        (
            "circumpolar", *OBSERVER, "--pole", "south",
            "--limiting-declination", "-40", "--horizon", "--horizon-mask",
            "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "circumpolar declination boundary crossing the observer horizon",
    ),
    MatrixEntry(
        "diagnostic-planisphere-horizon-noop",
        (
            "planisphere", *OBSERVER, "--horizon", "--horizon-mask",
            "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "planisphere horizon reference and mask remain idempotent no-ops",
    ),
    MatrixEntry(
        "diagnostic-legends-references-grids",
        (
            "regional", *OBSERVER, "--constellations", "Cru",
            "--altaz-grid", "--altaz-grid-labels",
            "--equatorial-grid", "--equatorial-grid-labels",
            "--ecliptic-grid", "--ecliptic-grid-labels",
            "--galactic-grid", "--galactic-grid-labels",
            "--grid-references", "all", "--poles", "--pole-labels",
            "--legends", "--star-counts", "--location", "--date",
            "--local-time", "--credits", "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "all grids, reference labels, poles, legends, context, and credits",
    ),
)


def _png_dimensions(path):
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"{path} is not a PNG image")
    return struct.unpack(">II", header[16:24])


def _commit():
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def render_matrix(destination, entries=MATRIX):
    """Render ``entries`` in isolated command processes and write a manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for index, entry in enumerate(entries, start=1):
        output = destination / f"{entry.name}.png"
        command = (
            sys.executable, "-m", "wenu.cli.chart",
            *entry.arguments, "--output", str(output),
        )
        print(f"[{index}/{len(entries)}] {entry.name}", flush=True)
        subprocess.run(command, check=True)
        width, height = _png_dimensions(output)
        records.append({
            **asdict(entry),
            "command": ("wenu_chart", *entry.arguments, "--output", str(output)),
            "output": str(output),
            "width": width,
            "height": height,
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
        default=Path("output/46d8-visual-matrix"),
    )
    value.add_argument(
        "--entry",
        action="append",
        choices=tuple(entry.name for entry in MATRIX),
        help="render only this matrix entry; repeat to select several",
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

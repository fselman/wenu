"""Render the Milestone 50A.3G explicit-CLI visual acceptance matrix."""

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
    "--observer-time", "2026-09-16T00:00:00Z",
)
PRODUCT = (
    "--magnitude-limit", "6.0",
    "--style", "atlas", "--mode", "presentation",
)


@dataclass(frozen=True)
class MatrixEntry:
    """One deterministic installed-command visual diagnostic."""

    name: str
    arguments: tuple[str, ...]
    proves: str
    requires_minor_body_resources: bool = False


def _regional(name, *arguments, proves, resources=False):
    return MatrixEntry(
        name,
        ("regional", *OBSERVER, *arguments, *PRODUCT),
        proves,
        resources,
    )


MATRIX = (
    _regional(
        "center-virgo-no-constellation-content",
        "--center-on", "constellation:Vir",
        proves="a constellation center enables no constellation layer",
    ),
    _regional(
        "center-virgo-draw-venus",
        "--center-on", "constellation:Vir", "--planet", "venus",
        proves="drawing Venus does not replace the Virgo center",
    ),
    _regional(
        "center-venus-draw-mask-virgo",
        "--center-on", "planet:Venus", "--planet", "venus",
        "--field-width", "40", "--field-height", "30",
        "--constellation-system", "western",
        "--constellation-lines", "Vir",
        "--constellation-labels", "Vir",
        "--constellation-mask", "Vir",
        proves=(
            "moving center, moving content, constellation content, and mask "
            "are independent"
        ),
    ),
    _regional(
        "center-icrs-coordinate",
        "--center-icrs-ra", "201.365deg",
        "--center-icrs-dec=-43.019deg", "--center-name", "ICRS field",
        "--field-width", "20", "--field-height", "15",
        proves="a unit-bearing ICRS pair defines one literal point center",
    ),
    _regional(
        "center-star-sirius",
        "--center-on", "star:Sirius",
        "--field-width", "20", "--field-height", "15",
        proves="a qualified star name centers without selecting star content",
    ),
    _regional(
        "center-galaxy-centaurus-a",
        "--center-on", "galaxy:Centaurus A",
        "--field-width", "20", "--field-height", "15",
        proves="a qualified galaxy name centers without selecting galaxy content",
    ),
    _regional(
        "center-cluster-omega-centauri",
        "--center-on", "cluster:Omega Centauri",
        "--field-width", "12", "--field-height", "9",
        proves="a qualified cluster name centers without selecting cluster content",
    ),
    _regional(
        "center-asteroid-79989",
        "--center-on", "asteroid:79989", "--asteroid", "79989",
        "--field-width", "20", "--field-height", "15",
        proves="installed asteroid center and drawing requests remain independent",
        resources=True,
    ),
    _regional(
        "center-virgo-draw-three-planets",
        "--center-on", "constellation:Vir",
        "--planet", "venus,mars,jupiter",
        proves="several drawn planets leave the explicit center unchanged",
    ),
    _regional(
        "center-sirius-celestial-north-up",
        "--center-on", "star:Sirius",
        "--field-width", "20", "--field-height", "15",
        "--orientation", "celestial-north-up",
        proves="celestial north is the explicit up direction",
    ),
    _regional(
        "center-sirius-zenith-up",
        "--center-on", "star:Sirius",
        "--field-width", "20", "--field-height", "15",
        "--orientation", "zenith-up",
        proves="local zenith is the explicit up direction",
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
        ("git", "rev-parse", "HEAD"), check=True,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def render_matrix(destination, entries, resource_directory=None):
    """Render ``entries`` in isolated command processes and write a manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    records = []
    for index, entry in enumerate(entries, start=1):
        if entry.requires_minor_body_resources and resource_directory is None:
            raise ValueError(
                "center-asteroid-79989 requires "
                "--minor-body-resource-directory"
            )
        output = destination / f"{entry.name}.png"
        resource_arguments = (
            ("--minor-body-resource-directory", str(resource_directory))
            if entry.requires_minor_body_resources else ()
        )
        arguments = (*entry.arguments, *resource_arguments)
        command = (
            sys.executable, "-m", "wenu.cli.chart",
            *arguments, "--output", str(output),
        )
        print(f"[{index}/{len(entries)}] {entry.name}", flush=True)
        subprocess.run(command, check=True)
        width, height = _png_dimensions(output)
        records.append({
            **asdict(entry),
            "command": ("wenu_chart", *arguments, "--output", str(output)),
            "output": str(output),
            "width": width,
            "height": height,
            "bytes": output.stat().st_size,
            "sha256": sha256(output.read_bytes()).hexdigest(),
        })
    manifest = destination / "manifest.json"
    manifest.write_text(json.dumps({
        "source_commit": _commit(),
        "entry_count": len(records),
        "entries": records,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--output", type=Path, default=Path("/tmp/wenu-50a3g"))
    value.add_argument("--minor-body-resource-directory", type=Path)
    value.add_argument(
        "--entry", action="append",
        choices=tuple(entry.name for entry in MATRIX),
        help="render only this matrix entry; repeat to select several",
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
    resource_directory = (
        None if arguments.minor_body_resource_directory is None
        else arguments.minor_body_resource_directory.expanduser()
    )
    print(render_matrix(arguments.output, entries, resource_directory))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

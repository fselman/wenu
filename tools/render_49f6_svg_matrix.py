"""Render and inspect the Milestone 49F.6 cross-product SVG matrix."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from wenu import (
    Observer,
    PolarCalendarFurnitureRequest,
    PolarHorizonOverlayRequest,
    PolarPageFurnitureRequest,
    PolarPlanispherePairRequest,
    PolarPouchFurnitureRequest,
    PolarPouchSheetRequest,
    default_polar_magnitude_scale,
    export_polar_planisphere_pages,
    export_polar_pouch_sheet,
    generate_celestial_sphere,
)


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
    """One deterministic SVG acceptance product."""

    name: str
    kind: str
    arguments: tuple[str, ...]
    proves: str


MATRIX = (
    MatrixEntry(
        "all-sky",
        "cli",
        (
            "all-sky", *OBSERVER, "--constellations", "Cru,Cyg,UMa",
            "--mask", "--constellation-lines", "--constellation-labels",
            "--constellation-boundaries", "--equatorial-grid",
            "--equatorial-grid-labels", "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "Mollweide boundary, seam geometry, disjoint masks, and labels",
    ),
    MatrixEntry(
        "planisphere",
        "cli",
        (
            "planisphere", *OBSERVER, "--constellation-lines",
            "--constellation-labels", "--equatorial-grid",
            "--equatorial-grid-labels", "--ecliptic-grid",
            "--ecliptic-grid-labels", "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "circular boundary, transparency, references, and labels",
    ),
    MatrixEntry(
        "regional",
        "cli",
        (
            "regional", *OBSERVER, "--constellations", "Cen,Cru,Mus",
            "--mask", "--field-width", "60", "--field-height", "45",
            "--orientation", "celestial-north-up",
            "--constellation-lines", "--constellation-labels",
            "--constellation-boundaries", "--equatorial-grid",
            "--equatorial-grid-labels", "--ecliptic-grid",
            "--ecliptic-grid-labels", "--galactic-grid",
            "--galactic-grid-labels", "--grid-references", "all",
            "--poles", "--pole-labels", "--legends", "--star-counts",
            "--location", "--date", "--local-time", "--credits",
            "--magnitude-limit", "5.0", "--style", "atlas",
            "--mode", "print",
        ),
        "rectangular mask, complete hierarchy, legends, and furniture",
    ),
    MatrixEntry(
        "circumpolar",
        "cli",
        (
            "circumpolar", *OBSERVER, "--pole", "south",
            "--limiting-declination", "-40", "--horizon",
            "--horizon-mask", "--constellation-lines",
            "--constellation-labels", "--equatorial-grid",
            "--equatorial-grid-labels", "--magnitude-limit", "5.0",
            "--style", "atlas", "--mode", "print",
        ),
        "declination boundary, horizon mask, circular clipping, and grid",
    ),
    MatrixEntry(
        "binocular",
        "cli",
        (
            "binocular", *BINOCULAR_OBSERVER, "--target", "centaurus-a",
            "--field-diameter", "6.5", "--orientation",
            "celestial-north-up", "--magnitude-limit", "11.0",
            "--legends", "--star-counts", "--style", "atlas",
            "--mode", "print",
        ),
        "small circular field, dense stars, symbols, and magnitude scale",
    ),
    MatrixEntry(
        "polar-pages",
        "polar-pages",
        (),
        "actual-size north and south disks, calendar, and page furniture",
    ),
    MatrixEntry(
        "polar-pouch",
        "polar-pouch",
        (),
        "actual-size imposed pouch, windows, hour scale, and fabrication marks",
    ),
)


def _source_revision():
    result = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _render_cli(entry, destination):
    output = destination / f"{entry.name}.svg"
    command = (
        sys.executable, "-m", "wenu.cli.chart", *entry.arguments,
        "--format", "svg", "--output", str(output),
        "--title", f"49F.6 {entry.name} SVG audit",
    )
    subprocess.run(command, check=True)
    return (output,), ("wenu_chart", *entry.arguments, "--format", "svg")


def _polar_values(source_revision):
    pair = PolarPlanispherePairRequest(
        calendar_radius_mm=86.0,
        pivot_radius_mm=1.0,
    ).resolve()
    magnitude_scale = default_polar_magnitude_scale()
    calendar = PolarCalendarFurnitureRequest().resolve(pair)
    pages = PolarPageFurnitureRequest(
        source_revision=source_revision
    ).resolve(pair, magnitude_scale=magnitude_scale)
    sky = generate_celestial_sphere()
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    return pair, magnitude_scale, calendar, pages, sky, observer


def _render_polar_pages(destination, source_revision):
    pair, _, calendar, pages, sky, observer = _polar_values(source_revision)
    outputs = (
        destination / "polar-page-south.svg",
        destination / "polar-page-north.svg",
    )
    try:
        export_polar_planisphere_pages(
            pair,
            calendar,
            pages,
            sky,
            observer,
            south_path=outputs[0],
            north_path=outputs[1],
        )
    finally:
        observer.close()
    return outputs, ("export_polar_planisphere_pages",)


def _render_polar_pouch(destination, source_revision):
    pair, magnitude_scale, calendar, pages, _, observer = _polar_values(
        source_revision
    )
    output = destination / "polar-pouch.svg"
    try:
        horizons = PolarHorizonOverlayRequest(
            site_latitude_deg=observer.lat_deg
        ).resolve(pair, pages, observer)
        pouches = PolarPouchFurnitureRequest().resolve(
            horizons,
            magnitude_scale=magnitude_scale,
        )
        sheet = PolarPouchSheetRequest(spine_width_mm=1.0).resolve(pouches)
        export_polar_pouch_sheet(
            sheet,
            pouches,
            output,
            source_revision=source_revision,
        )
    finally:
        observer.close()
    return (output,), ("export_polar_pouch_sheet",)


def inspect_svg(path):
    """Return backend-tolerant structural facts for one SVG product."""
    root = ET.parse(path).getroot()
    elements = tuple(root.iter())
    ids = [element.get("id") for element in elements if element.get("id")]
    duplicate_ids = sorted(
        item for item, count in Counter(ids).items() if count > 1
    )
    semantic_artists = [
        element for element in elements
        if "wenu-semantic-artist" in element.get("class", "").split()
    ]
    semantic_groups = [
        element for element in elements
        if "wenu-semantic-group" in element.get("class", "").split()
    ]
    tags = Counter(element.tag.rsplit("}", 1)[-1] for element in elements)
    policies = Counter(
        element.get("data-wenu-edit", "<missing>")
        for element in semantic_artists
    )
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path.read_bytes()).hexdigest(),
        "width": root.get("width"),
        "height": root.get("height"),
        "view_box": root.get("viewBox"),
        "text_elements": tags["text"],
        "image_elements": tags["image"],
        "metadata_elements": tags["metadata"],
        "semantic_artists": len(semantic_artists),
        "semantic_groups": len(semantic_groups),
        "edit_policies": dict(sorted(policies.items())),
        "missing_semantic_paths": sum(
            element.get("data-wenu-semantic-path") is None
            for element in (*semantic_artists, *semantic_groups)
        ),
        "duplicate_ids": duplicate_ids,
    }


def render_matrix(destination, entries=MATRIX):
    """Render selected products and write their structural audit manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    source_revision = _source_revision()
    records = []
    for index, entry in enumerate(entries, start=1):
        print(f"[{index}/{len(entries)}] {entry.name}", flush=True)
        if entry.kind == "cli":
            outputs, command = _render_cli(entry, destination)
        elif entry.kind == "polar-pages":
            outputs, command = _render_polar_pages(
                destination, source_revision
            )
        elif entry.kind == "polar-pouch":
            outputs, command = _render_polar_pouch(
                destination, source_revision
            )
        else:
            raise ValueError(f"Unsupported matrix kind {entry.kind!r}.")
        records.append({
            **asdict(entry),
            "command": command,
            "outputs": [inspect_svg(path) for path in outputs],
        })
    manifest = destination / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "source_revision": source_revision,
                "entry_count": len(records),
                "entries": records,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    return manifest


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/49f6-svg-matrix"),
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


if __name__ == "__main__":
    main()

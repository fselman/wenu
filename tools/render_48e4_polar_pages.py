"""Render actual-size Milestone 48E.4 north/south classroom pages."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

from wenu import (
    Observer,
    PolarCalendarFurnitureRequest,
    PolarPageFurnitureRequest,
    PolarPlanispherePairRequest,
    export_polar_planisphere_pages,
    generate_celestial_sphere,
)


def render_pages(destination, *, source_revision, projection_name, dpi=300):
    """Render two actual-size PDFs and a deterministic checksum manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    pair = PolarPlanispherePairRequest(
        projection_name=projection_name,
        calendar_radius_mm=86.0,
        pivot_radius_mm=1.0,
    ).resolve()
    calendar = PolarCalendarFurnitureRequest().resolve(pair)
    pages = PolarPageFurnitureRequest(
        source_revision=source_revision
    ).resolve(pair)
    sky = generate_celestial_sphere()
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    south = destination / "polar-planisphere-south-a4.pdf"
    north = destination / "polar-planisphere-north-a4.pdf"
    try:
        result = export_polar_planisphere_pages(
            pair,
            calendar,
            pages,
            sky,
            observer,
            south_path=south,
            north_path=north,
            dpi=dpi,
        )
    finally:
        observer.close()
    outputs = tuple(item.output for item in result.faces)
    manifest = destination / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "page_size_mm": [210.0, 297.0],
                "disk_diameter_mm": 195.0,
                "stellar_aperture_diameter_mm": (
                    2.0 * calendar.south.star_disk_radius_mm
                ),
                "projection": projection_name,
                "source_revision": source_revision,
                "dpi": int(dpi),
                "outputs": [
                    {
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "sha256": sha256(path.read_bytes()).hexdigest(),
                    }
                    for path in outputs
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return outputs, manifest


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/48e4-polar-pages"),
    )
    value.add_argument("--source-revision", required=True)
    value.add_argument(
        "--projection",
        choices=("polar_azimuthal_equidistant", "stereographic"),
        default="polar_azimuthal_equidistant",
    )
    value.add_argument("--dpi", type=int, default=300)
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    outputs, manifest = render_pages(
        arguments.output,
        source_revision=arguments.source_revision,
        projection_name=arguments.projection,
        dpi=arguments.dpi,
    )
    print(*(str(path) for path in (*outputs, manifest)), sep="\n")


if __name__ == "__main__":
    main()

"""Render the actual-size folded polar-pouch front and back."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from matplotlib import image as matplotlib_image

from wenu import (
    Observer,
    PolarCalendarFurnitureRequest,
    PolarHorizonOverlayRequest,
    PolarPageFurnitureRequest,
    PolarPlanispherePairRequest,
    PolarPouchFurnitureRequest,
    PolarPouchSheetRequest,
    compose_polar_pouch_sheet_preview,
    export_polar_planisphere_pages,
    export_polar_pouch_sheet,
    generate_celestial_sphere,
)


def render_pouch(destination, *, source_revision, title, dpi=300):
    """Write paired PDF/PNG faces and a deterministic checksum manifest."""
    destination.mkdir(parents=True, exist_ok=True)
    pair = PolarPlanispherePairRequest(
        calendar_radius_mm=86.0,
        pivot_radius_mm=1.0,
    ).resolve()
    calendar = PolarCalendarFurnitureRequest().resolve(pair)
    pages = PolarPageFurnitureRequest(
        source_revision=source_revision
    ).resolve(pair)
    sky = generate_celestial_sphere()
    observer = Observer(location="La Ligua", time="2026-08-15 21:00")
    try:
        horizons = PolarHorizonOverlayRequest(
            site_latitude_deg=observer.lat_deg
        ).resolve(pair, pages, observer)
        pouches = PolarPouchFurnitureRequest(south_title=title).resolve(
            horizons
        )
        sheet = PolarPouchSheetRequest(spine_width_mm=1.0).resolve(pouches)
        disk_rotations = _diagnostic_disk_rotations(
            calendar,
            pouches,
            month=8,
            day=15,
            hour=21,
        )
        pdf_path = destination / "polar-pouch-single-sheet-a4.pdf"
        png_path = destination / "polar-pouch-single-sheet-a4.png"
        with TemporaryDirectory(prefix="wenu-pouch-preview-") as temporary:
            temporary = Path(temporary)
            pdf = export_polar_pouch_sheet(
                sheet,
                pouches,
                pdf_path,
                source_revision=source_revision,
                dpi=dpi,
            )
            clean_pouch_path = temporary / "pouch-sheet.png"
            disk_paths = (
                temporary / "disk-south.png",
                temporary / "disk-north.png",
            )
            export_polar_pouch_sheet(
                sheet,
                pouches,
                clean_pouch_path,
                source_revision=source_revision,
                dpi=dpi,
            )
            export_polar_planisphere_pages(
                pair,
                calendar,
                pages,
                sky,
                observer,
                south_path=disk_paths[0],
                north_path=disk_paths[1],
                dpi=dpi,
            )
            preview = compose_polar_pouch_sheet_preview(
                tuple(matplotlib_image.imread(path) for path in disk_paths),
                matplotlib_image.imread(clean_pouch_path),
                pages=pages,
                sheet=sheet,
                disk_rotation_deg=disk_rotations,
            )
            matplotlib_image.imsave(png_path, preview, dpi=dpi)
    finally:
        observer.close()
    outputs = (pdf.output, png_path)
    manifest = destination / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "page_size_mm": [210.0, 297.0],
                "disk_diameter_mm": 195.0,
                "disk_center_mm": list(pouches.south.disk_center_mm),
                "fold_lines_y_mm": [
                    sheet.lower_fold_y_mm,
                    sheet.upper_fold_y_mm,
                ],
                "single_sheet": {
                    "south_panel": "top",
                    "north_panel": "bottom, rotated 180 degrees",
                    "spine_width_mm": sheet.spine_width_mm,
                    "panel_depth_mm": sheet.panel_depth_mm,
                    "disk_protrusion_mm": sheet.disk_protrusion_mm,
                    "load_after_assembly": True,
                },
                "diagnostic_registration": {
                    "month": 8,
                    "day": 15,
                    "hour": 21,
                    "disk_rotation_deg": list(disk_rotations),
                },
                "date_windows": {
                    "count": 3,
                    "span_deg": 37.5,
                    "gap_deg": 5.0,
                },
                "hours": [19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5],
                "duplex_instruction": "Print actual size, flip on long edge",
                "source_revision": source_revision,
                "south_title": title,
                "dpi": int(dpi),
                "png_preview": {
                    "canonical_disk_opacity": 0.18,
                    "fabrication_pdfs_are_clean": True,
                },
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


def _diagnostic_disk_rotations(
    calendar,
    pouches,
    *,
    month,
    day,
    hour,
):
    rotations = []
    for calendar_face, pouch_face in zip(
        calendar.faces, pouches.faces, strict=True
    ):
        date_tick = next(
            tick
            for tick in calendar_face.ticks
            if tick.month == int(month) and tick.day == int(day)
        )
        hour_mark = next(
            mark for mark in pouch_face.hour_marks if mark.hour == int(hour)
        )
        rotations.append(
            (hour_mark.angle_deg - date_tick.angle_deg) % 360.0
        )
    return tuple(rotations)


def parser():
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument(
        "--output",
        type=Path,
        default=Path("output/48g2-polar-pouch"),
    )
    value.add_argument("--source-revision", required=True)
    value.add_argument(
        "--title",
        default="Muchos cielos, un firmamento",
        help="South-panel title.",
    )
    value.add_argument("--dpi", type=int, default=300)
    return value


def main(argv=None):
    arguments = parser().parse_args(argv)
    outputs, manifest = render_pouch(
        arguments.output,
        source_revision=arguments.source_revision,
        title=arguments.title,
        dpi=arguments.dpi,
    )
    print(*(str(path) for path in (*outputs, manifest)), sep="\n")


if __name__ == "__main__":
    main()

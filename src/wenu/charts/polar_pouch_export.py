"""Actual-size export of paired folded polar-pouch faces."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt

from wenu.charts.polar_pouch_furniture import PolarPouchPairFurniture
from wenu.charts.polar_pouch_rendering import draw_polar_pouch_face
from wenu.charts.regional import ExportOptions


MM_PER_INCH = 25.4


@dataclass(frozen=True)
class PolarPouchFaceExportResult:
    """One rendered and saved physical pouch face."""

    face: str
    rendering: object
    output: object
    export_options: ExportOptions


@dataclass(frozen=True)
class PolarPouchPairExportResult:
    """Paired south-front and north-back pouch exports."""

    south: PolarPouchFaceExportResult
    north: PolarPouchFaceExportResult

    @property
    def faces(self):
        return self.south, self.north


def export_polar_pouch_pages(
    pouches,
    *,
    south_path,
    north_path,
    source_revision,
    dpi=300,
):
    """Render and save one actual-size A4 output per pouch face."""
    if not isinstance(pouches, PolarPouchPairFurniture):
        raise TypeError("pouches must be a PolarPouchPairFurniture value.")
    source_revision = str(source_revision).strip()
    if not source_revision:
        raise ValueError("source_revision is required for printable pages.")
    if int(dpi) <= 0:
        raise ValueError("dpi must be positive.")
    south = _export_face(
        pouches.south,
        south_path,
        source_revision=source_revision,
        dpi=int(dpi),
    )
    north = _export_face(
        pouches.north,
        north_path,
        source_revision=source_revision,
        dpi=int(dpi),
    )
    return PolarPouchPairExportResult(south=south, north=north)


def _export_face(face, destination, *, source_revision, dpi):
    width_inches = face.page_size_mm[0] / MM_PER_INCH
    height_inches = face.page_size_mm[1] / MM_PER_INCH
    figure = plt.figure(
        figsize=(width_inches, height_inches),
        facecolor="white",
    )
    # Some older Matplotlib releases quantize ``figsize`` during Figure
    # construction.  Restore the physical contract explicitly before drawing.
    figure.set_size_inches(width_inches, height_inches, forward=False)
    options = ExportOptions(
        dpi=dpi,
        bbox_inches=None,
        transparent=False,
        facecolor="white",
        metadata={
            "Title": f"Wenu folded polar pouch — {face.face}",
            "Creator": "Wenu",
            "Subject": f"Source revision {source_revision}",
        },
        padding=0.0,
    )
    try:
        rendering = draw_polar_pouch_face(face, figure=figure)
        output = options.save(figure, destination)
    finally:
        plt.close(figure)
    return PolarPouchFaceExportResult(
        face=face.face,
        rendering=rendering,
        output=output,
        export_options=options,
    )

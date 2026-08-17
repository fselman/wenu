"""Actual-size export of one imposed folded polar-pouch sheet."""

from __future__ import annotations

from dataclasses import dataclass

import matplotlib.pyplot as plt

from wenu.charts.polar_pouch_furniture import PolarPouchPairFurniture
from wenu.charts.polar_pouch_sheet import PolarPouchSheetFurniture
from wenu.charts.polar_pouch_sheet_rendering import draw_polar_pouch_sheet
from wenu.charts.regional import ExportOptions


@dataclass(frozen=True)
class PolarPouchSheetExportResult:
    """One rendered and saved single-sheet fabrication product."""

    rendering: object
    output: object
    export_options: ExportOptions


def export_polar_pouch_sheet(
    sheet,
    pouches,
    destination,
    *,
    source_revision,
    dpi=300,
):
    """Render and save one actual-size A4 folded-pouch sheet."""
    if not isinstance(sheet, PolarPouchSheetFurniture):
        raise TypeError("sheet must be a PolarPouchSheetFurniture value.")
    if not isinstance(pouches, PolarPouchPairFurniture):
        raise TypeError("pouches must be a PolarPouchPairFurniture value.")
    source_revision = str(source_revision).strip()
    if not source_revision:
        raise ValueError("source_revision is required for printable sheets.")
    if int(dpi) <= 0:
        raise ValueError("dpi must be positive.")
    width = sheet.page_size_mm[0] / 25.4
    height = sheet.page_size_mm[1] / 25.4
    figure = plt.figure(figsize=(width, height), facecolor="white")
    figure.set_size_inches(width, height, forward=False)
    options = ExportOptions(
        dpi=int(dpi),
        bbox_inches=None,
        transparent=False,
        facecolor="white",
        metadata={
            "Title": "Wenu single-sheet folded polar pouch",
            "Creator": "Wenu",
            "Subject": f"Source revision {source_revision}",
        },
        padding=0.0,
    )
    try:
        rendering = draw_polar_pouch_sheet(sheet, pouches, figure=figure)
        output = options.save(figure, destination)
    finally:
        plt.close(figure)
    return PolarPouchSheetExportResult(
        rendering=rendering,
        output=output,
        export_options=options,
    )

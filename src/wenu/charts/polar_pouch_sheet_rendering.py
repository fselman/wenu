"""Vector rendering of both pouch faces on one folded A4 sheet."""

from __future__ import annotations

from dataclasses import dataclass

from wenu.charts.polar_pouch_furniture import PolarPouchPairFurniture
from wenu.charts.polar_pouch_rendering import draw_polar_pouch_face
from wenu.charts.polar_pouch_sheet import PolarPouchSheetFurniture


@dataclass(frozen=True)
class PolarPouchSheetRendering:
    """Inspectable paired face renderings and central folding spine."""

    page_axes: object
    south: object
    north: object
    fold_lines: tuple[object, object]


def draw_polar_pouch_sheet(sheet, pouches, *, figure=None):
    """Draw one top-south/bottom-north fabrication sheet without saving."""
    if not isinstance(sheet, PolarPouchSheetFurniture):
        raise TypeError("sheet must be a PolarPouchSheetFurniture value.")
    if not isinstance(pouches, PolarPouchPairFurniture):
        raise TypeError("pouches must be a PolarPouchPairFurniture value.")
    if figure is None:
        import matplotlib.pyplot as plt

        figure = plt.figure(
            figsize=(
                sheet.page_size_mm[0] / 25.4,
                sheet.page_size_mm[1] / 25.4,
            ),
            facecolor="white",
        )
    from matplotlib.transforms import Affine2D

    ax = figure.add_axes((0.0, 0.0, 1.0, 1.0), label="polar_pouch_sheet")
    ax.set_xlim(0.0, sheet.page_size_mm[0])
    ax.set_ylim(0.0, sheet.page_size_mm[1])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_facecolor("white")
    south_transform = Affine2D().translate(*sheet.south.translation_mm)
    north_transform = (
        Affine2D()
        .rotate_deg(sheet.north.rotation_deg)
        .translate(*sheet.north.translation_mm)
    )
    south = draw_polar_pouch_face(
        pouches.south,
        axes=ax,
        artist_transform=south_transform,
        clip_bounds_mm=sheet.south.clip_bounds_mm,
    )
    north = draw_polar_pouch_face(
        pouches.north,
        axes=ax,
        artist_transform=north_transform,
        clip_bounds_mm=sheet.north.clip_bounds_mm,
    )
    for text in (
        *north.hour_labels,
        *north.labels,
        north.magnitude_scale.title,
        *north.magnitude_scale.labels,
    ):
        text.set_rotation(float(text.get_rotation()) + 180.0)
    return PolarPouchSheetRendering(
        page_axes=ax,
        south=south,
        north=north,
        fold_lines=(south.fold_line, north.fold_line),
    )

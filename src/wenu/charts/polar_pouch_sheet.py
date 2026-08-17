"""Single-A4 imposition of the paired folded polar-pouch faces."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from wenu.charts.polar_pouch_furniture import PolarPouchPairFurniture


@dataclass(frozen=True)
class PolarPouchPanelPlacement:
    """One pouch face placed and clipped on the common fabrication sheet."""

    face: str
    rotation_deg: float
    translation_mm: tuple[float, float]
    clip_bounds_mm: tuple[float, float, float, float]
    face_disk_center_mm: tuple[float, float]


@dataclass(frozen=True)
class PolarPouchSheetFurniture:
    """Resolved one-sided A4 sheet with a central folding spine."""

    page_size_mm: tuple[float, float]
    spine_width_mm: float
    lower_fold_y_mm: float
    upper_fold_y_mm: float
    panel_depth_mm: float
    disk_protrusion_mm: float
    south: PolarPouchPanelPlacement
    north: PolarPouchPanelPlacement

    @property
    def placements(self):
        return self.south, self.north

    @property
    def fold_lines_mm(self):
        width = self.page_size_mm[0]
        return (
            ((0.0, self.lower_fold_y_mm), (width, self.lower_fold_y_mm)),
            ((0.0, self.upper_fold_y_mm), (width, self.upper_fold_y_mm)),
        )


@dataclass(frozen=True)
class PolarPouchSheetRequest:
    """Resolve top-south/bottom-north imposition on one portrait A4 sheet."""

    spine_width_mm: float = 1.0

    def __post_init__(self):
        width = float(self.spine_width_mm)
        if not np.isfinite(width) or width <= 0.0:
            raise ValueError("spine_width_mm must be positive and finite.")
        object.__setattr__(self, "spine_width_mm", width)

    def resolve(self, pouches):
        """Return an imposed sheet without changing either face geometry."""
        if not isinstance(pouches, PolarPouchPairFurniture):
            raise TypeError("pouches must be a PolarPouchPairFurniture value.")
        if pouches.south.page_size_mm != pouches.north.page_size_mm:
            raise ValueError("Paired pouch faces require one page size.")
        page_width, page_height = pouches.south.page_size_mm
        panel_depth = (page_height - self.spine_width_mm) / 2.0
        lower_fold = panel_depth
        upper_fold = lower_fold + self.spine_width_mm
        radius = pouches.south.disk_radius_mm
        diameter = 2.0 * radius
        if panel_depth >= diameter:
            raise ValueError("The imposed disk must protrude from the sleeve.")
        south = PolarPouchPanelPlacement(
            face="south",
            rotation_deg=0.0,
            translation_mm=(0.0, upper_fold - pouches.south.fold_y_mm),
            clip_bounds_mm=(0.0, upper_fold, page_width, page_height),
            face_disk_center_mm=pouches.south.disk_center_mm,
        )
        north = PolarPouchPanelPlacement(
            face="north",
            rotation_deg=180.0,
            translation_mm=(
                page_width,
                lower_fold + pouches.north.fold_y_mm,
            ),
            clip_bounds_mm=(0.0, 0.0, page_width, lower_fold),
            face_disk_center_mm=pouches.north.disk_center_mm,
        )
        return PolarPouchSheetFurniture(
            page_size_mm=(page_width, page_height),
            spine_width_mm=self.spine_width_mm,
            lower_fold_y_mm=lower_fold,
            upper_fold_y_mm=upper_fold,
            panel_depth_mm=panel_depth,
            disk_protrusion_mm=diameter - panel_depth,
            south=south,
            north=north,
        )

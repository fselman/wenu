"""Typed paint-order roles shared by chart rendering and documents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class PaintRole:
    """One stable semantic role in Wenu's established paint order."""

    zorder: float
    name: str

    @property
    def svg_token(self):
        return self.name.replace("_", "-")


BACKGROUND = PaintRole(0.0, "background")
MILKY_WAY = PaintRole(1.0, "milky_way")
MAGELLANIC_CLOUDS = PaintRole(1.1, "magellanic_clouds")
GALAXY_FILLS = PaintRole(1.5, "galaxy_fills")
BOUNDARIES = PaintRole(2.0, "boundaries")
CURVES = PaintRole(3.0, "curves")
CONSTELLATIONS = PaintRole(4.0, "constellations")
GALAXIES = PaintRole(4.5, "galaxies")
SUPERNOVA_REMNANTS = PaintRole(4.6, "supernova_remnants")
PLANETARY_NEBULAE = PaintRole(4.7, "planetary_nebulae")
OPEN_CLUSTERS = PaintRole(4.72, "open_clusters")
GLOBULAR_CLUSTERS = PaintRole(4.75, "globular_clusters")
STARS = PaintRole(5.0, "stars")
BRIGHT_STARS = PaintRole(5.05, "bright_stars")
MULTIPLE_STARS = PaintRole(5.1, "multiple_stars")
VARIABLE_STARS = PaintRole(5.2, "variable_stars")
POINTS = PaintRole(6.0, "points")
LABELS = PaintRole(7.0, "labels")
OUTSIDE_MASKS = PaintRole(20.0, "outside_masks")

PAINT_ROLES = (
    BACKGROUND,
    MILKY_WAY,
    MAGELLANIC_CLOUDS,
    GALAXY_FILLS,
    BOUNDARIES,
    CURVES,
    CONSTELLATIONS,
    GALAXIES,
    SUPERNOVA_REMNANTS,
    PLANETARY_NEBULAE,
    OPEN_CLUSTERS,
    GLOBULAR_CLUSTERS,
    STARS,
    BRIGHT_STARS,
    MULTIPLE_STARS,
    VARIABLE_STARS,
    POINTS,
    LABELS,
    OUTSIDE_MASKS,
)
_BY_ZORDER = {role.zorder: role for role in PAINT_ROLES}


def paint_role_for_zorder(zorder) -> PaintRole | None:
    """Return the exact documented role for a numeric paint position."""
    try:
        value = float(zorder)
    except (TypeError, ValueError):
        return None
    return _BY_ZORDER.get(value)

"""Typed paint-order roles shared by chart rendering and documents."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class PaintBand:
    """A coarse stacking band that may contain several paint roles."""

    rank: int
    name: str

    @property
    def svg_token(self):
        return self.name.replace("_", "-")


BACKGROUND_BAND = PaintBand(0, "background")
EXTENDED_SKY_BAND = PaintBand(1, "extended_sky")
STRUCTURE_BAND = PaintBand(2, "structure")
CONSTELLATION_BAND = PaintBand(3, "constellations")
OBJECT_BAND = PaintBand(4, "objects")
STAR_BAND = PaintBand(5, "stars")
POINT_BAND = PaintBand(6, "points")
LABEL_BAND = PaintBand(7, "labels")
OVERLAY_BAND = PaintBand(8, "overlays")

PAINT_BANDS = (
    BACKGROUND_BAND,
    EXTENDED_SKY_BAND,
    STRUCTURE_BAND,
    CONSTELLATION_BAND,
    OBJECT_BAND,
    STAR_BAND,
    POINT_BAND,
    LABEL_BAND,
    OVERLAY_BAND,
)


@dataclass(frozen=True)
class PaintRole:
    """One stable semantic role in Wenu's established paint order."""

    zorder: float
    name: str
    band: PaintBand

    @property
    def svg_token(self):
        return self.name.replace("_", "-")


BACKGROUND = PaintRole(0.0, "background", BACKGROUND_BAND)
MILKY_WAY = PaintRole(1.0, "milky_way", EXTENDED_SKY_BAND)
MAGELLANIC_CLOUDS = PaintRole(1.1, "magellanic_clouds", EXTENDED_SKY_BAND)
GALAXY_FILLS = PaintRole(1.5, "galaxy_fills", EXTENDED_SKY_BAND)
BOUNDARIES = PaintRole(2.0, "boundaries", STRUCTURE_BAND)
CURVES = PaintRole(3.0, "curves", STRUCTURE_BAND)
CONSTELLATIONS = PaintRole(4.0, "constellations", CONSTELLATION_BAND)
GALAXIES = PaintRole(4.5, "galaxies", OBJECT_BAND)
SUPERNOVA_REMNANTS = PaintRole(4.6, "supernova_remnants", OBJECT_BAND)
PLANETARY_NEBULAE = PaintRole(4.7, "planetary_nebulae", OBJECT_BAND)
OPEN_CLUSTERS = PaintRole(4.72, "open_clusters", OBJECT_BAND)
GLOBULAR_CLUSTERS = PaintRole(4.75, "globular_clusters", OBJECT_BAND)
STARS = PaintRole(5.0, "stars", STAR_BAND)
BRIGHT_STARS = PaintRole(5.05, "bright_stars", STAR_BAND)
MULTIPLE_STARS = PaintRole(5.1, "multiple_stars", STAR_BAND)
VARIABLE_STARS = PaintRole(5.2, "variable_stars", STAR_BAND)
POINTS = PaintRole(6.0, "points", POINT_BAND)
LABELS = PaintRole(7.0, "labels", LABEL_BAND)
OUTSIDE_MASKS = PaintRole(20.0, "outside_masks", OVERLAY_BAND)

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

"""Authoritative geometrical defaults for ordinary chart views."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ChartViewDefaults:
    """One public family policy containing geometry choices only."""

    family: str
    framing: str
    projection: str = "stereographic"
    coordinate_frame: str = "horizontal"
    orientation: str | None = None
    position_angle_deg: float | None = None
    mask: bool = False
    field_diameter_deg: float | None = None
    field_width_deg: float | None = None
    field_height_deg: float | None = None
    pole: str | None = None
    limiting_declination_deg: float | None = None


CHART_VIEW_DEFAULTS = MappingProxyType({
    "binocular": ChartViewDefaults(
        family="binocular",
        framing="fixed-diameter",
        field_diameter_deg=6.5,
        orientation="celestial-north-up",
    ),
    "regional-single": ChartViewDefaults(
        family="regional",
        framing="constellation-geometry",
        orientation="celestial-north-up",
    ),
    "regional-group": ChartViewDefaults(
        family="regional",
        framing="packaged-group",
        orientation="celestial-north-up",
    ),
    "planisphere": ChartViewDefaults(
        family="planisphere",
        framing="visible-hemisphere",
        position_angle_deg=0.0,
    ),
    "all_sky": ChartViewDefaults(
        family="all_sky",
        framing="complete-sphere",
        projection="mollweide",
        coordinate_frame="galactic",
        position_angle_deg=0.0,
    ),
    "circumpolar": ChartViewDefaults(
        family="circumpolar",
        framing="declination-limit",
        pole="south",
        limiting_declination_deg=-69.75,
        position_angle_deg=0.0,
    ),
})


def _geometry_detail_defaults():
    from wenu.configuration.geometry_detail_translation import (
        packaged_geometry_detail_defaults,
    )

    return packaged_geometry_detail_defaults()


def chart_view_defaults(family, *, group=False, configuration=None):
    """Return the immutable ordinary geometrical policy for a family."""
    normalized = str(family).strip().lower()
    key = (
        "regional-group"
        if normalized == "regional" and bool(group)
        else "regional-single"
        if normalized == "regional"
        else normalized
    )
    try:
        defaults = (
            _geometry_detail_defaults()
            if configuration is None
            else configuration.geometry_detail
        )
        return defaults.view_defaults[key]
    except KeyError as error:
        raise ValueError(
            "family must be planisphere, all_sky, regional, circumpolar, "
            "or binocular."
        ) from error

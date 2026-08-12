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
    position_angle_deg: float = 0.0
    mask: bool = False
    field_diameter_deg: float | None = None
    pole: str | None = None
    limiting_declination_deg: float | None = None


CHART_VIEW_DEFAULTS = MappingProxyType({
    "binocular": ChartViewDefaults(
        family="binocular",
        framing="fixed-diameter",
        field_diameter_deg=6.5,
    ),
    "regional-single": ChartViewDefaults(
        family="regional",
        framing="constellation-geometry",
    ),
    "regional-group": ChartViewDefaults(
        family="regional",
        framing="packaged-group",
    ),
    "planisphere": ChartViewDefaults(
        family="planisphere",
        framing="visible-hemisphere",
    ),
    "circumpolar": ChartViewDefaults(
        family="circumpolar",
        framing="declination-limit",
        pole="south",
        limiting_declination_deg=-69.75,
    ),
})


def chart_view_defaults(family, *, group=False):
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
        return CHART_VIEW_DEFAULTS[key]
    except KeyError as error:
        raise ValueError(
            "family must be planisphere, regional, circumpolar, or "
            "binocular."
        ) from error

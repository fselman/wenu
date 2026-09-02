"""Catalog-governed output-neutral physical identity for the Moon."""

from __future__ import annotations

from wenu.sky.solar_system_bodies import (
    RESOLVED_SPHERICAL_DISK,
    SPHERICAL_PHYSICAL_APPEARANCE,
    SYMBOLIC_POINT,
    SolarSystemBodyDescriptor,
)
from wenu.sky.solar_system_points import SolarSystemPointLayer


MOON_NAIF_BODY_ID = "301"
MOON_MEAN_RADIUS_KM = 1737.4
MOON_RADIUS_MODEL = (
    "JPL Planetary Satellite Physical Parameters equal-volume mean "
    "radius 1737.4 km"
)
MOON_BODY = SolarSystemBodyDescriptor(
    target="moon",
    entity_key="moon",
    display_name="Moon",
    selection_key="moon",
    body_class="natural_satellite",
    physical_body_id=MOON_NAIF_BODY_ID,
    parent_body_key="earth",
    classifications=frozenset({"natural_satellite"}),
    physical_radius_km=MOON_MEAN_RADIUS_KM,
    radius_model=MOON_RADIUS_MODEL,
    localized_display_names=(("en", "Moon"), ("es", "Luna")),
    capabilities=frozenset({
        SYMBOLIC_POINT,
        SPHERICAL_PHYSICAL_APPEARANCE,
        RESOLVED_SPHERICAL_DISK,
    }),
    resolved_disk_chart_families=frozenset({
        "regional", "binocular", "circumpolar", "planisphere", "all_sky",
    }),
)

# Preserve the accepted symbolic-layer descriptor import.
MOON_POINT = MOON_BODY


class MoonLayer(SolarSystemPointLayer):
    """Realize the apparent Moon through shared Solar-System orchestration."""

    layer_name = "moon"

    def __init__(self, **dependencies):
        super().__init__(MOON_BODY, **dependencies)

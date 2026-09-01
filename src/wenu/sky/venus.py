"""Configured symbolic-point specialization for apparent Venus."""

from __future__ import annotations

from wenu.sky.solar_system_bodies import (
    APPARENT_TRACK,
    FROZEN_EARTH_DISK_SEQUENCE,
    OBSERVED_DISK_SEQUENCE,
    RESOLVED_SPHERICAL_DISK,
    SYMBOLIC_POINT,
    SolarSystemBodyDescriptor,
)
from wenu.sky.solar_system_points import SolarSystemPointLayer
from wenu.solar_system_appearance import VENUS_MEAN_RADIUS_KM


VENUS_RADIUS_MODEL = (
    "JPL Planetary Physical Parameters mean radius 6051.8 km"
)
VENUS_POINT = SolarSystemBodyDescriptor(
    target="venus",
    entity_key="venus",
    display_name="Venus",
    selection_key="venus",
    body_class="planet",
    physical_body_id="299",
    classifications=frozenset({"planet"}),
    physical_radius_km=VENUS_MEAN_RADIUS_KM,
    radius_model=VENUS_RADIUS_MODEL,
    localized_display_names=(("en", "Venus"), ("es", "Venus")),
    capabilities=frozenset({
        SYMBOLIC_POINT,
        APPARENT_TRACK,
        RESOLVED_SPHERICAL_DISK,
        OBSERVED_DISK_SEQUENCE,
        FROZEN_EARTH_DISK_SEQUENCE,
    }),
)

class VenusLayer(SolarSystemPointLayer):
    """Realize apparent Venus through shared Solar-System orchestration."""

    layer_name = "venus"

    def __init__(self, **dependencies):
        super().__init__(VENUS_POINT, **dependencies)

"""Descriptor-only physical identity for output-neutral Mercury state."""

from wenu.sky.solar_system_bodies import (
    FROZEN_EARTH_DISK_SEQUENCE,
    SolarSystemBodyDescriptor,
)


MERCURY_NAIF_BODY_ID = "199"
MERCURY_MEAN_RADIUS_KM = 2439.4
MERCURY_RADIUS_MODEL = (
    "JPL Planetary Physical Parameters equal-volume mean radius 2439.4 km"
)
MERCURY_BODY = SolarSystemBodyDescriptor(
    target="mercury",
    entity_key="mercury",
    display_name="Mercury",
    selection_key="mercury",
    body_class="planet",
    physical_body_id=MERCURY_NAIF_BODY_ID,
    classifications=frozenset({"planet"}),
    physical_radius_km=MERCURY_MEAN_RADIUS_KM,
    radius_model=MERCURY_RADIUS_MODEL,
    localized_display_names=(("en", "Mercury"), ("es", "Mercurio")),
    capabilities=frozenset({FROZEN_EARTH_DISK_SEQUENCE}),
)

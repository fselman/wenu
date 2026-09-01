"""Output-neutral physical identity for Mercury."""

from wenu.sky.solar_system_points import SolarSystemPointDescriptor


MERCURY_NAIF_BODY_ID = "199"
MERCURY_RADIUS_MODEL = (
    "JPL Planetary Physical Parameters equal-volume mean radius"
)
MERCURY_POINT = SolarSystemPointDescriptor(
    target="mercury",
    entity_key="mercury",
    display_name="Mercury",
    selection_key="mercury",
)

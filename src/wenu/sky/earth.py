"""Non-drawable Earth identity for moving-body relationships."""

from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor


EARTH_NAIF_BODY_ID = "399"
EARTH_BODY = SolarSystemBodyDescriptor(
    target="earth",
    entity_key="earth",
    display_name="Earth",
    selection_key="earth",
    body_class="planet",
    physical_body_id=EARTH_NAIF_BODY_ID,
    classifications=frozenset({"planet"}),
    localized_display_names=(("en", "Earth"), ("es", "Tierra")),
)

"""Catalog data for ordinary apparent major-planet symbolic points."""

from wenu.sky.solar_system_bodies import (
    SYMBOLIC_POINT,
    SolarSystemBodyDescriptor,
)


def _planet(
    *,
    target,
    entity_key,
    display_name,
    spanish_name,
    physical_body_id,
    astronomical_symbol,
):
    return SolarSystemBodyDescriptor(
        target=target,
        entity_key=entity_key,
        display_name=display_name,
        selection_key=entity_key,
        body_class="planet",
        physical_body_id=physical_body_id,
        astronomical_symbol=astronomical_symbol,
        classifications=frozenset({"planet"}),
        capabilities=frozenset({SYMBOLIC_POINT}),
        localized_display_names=(
            ("en", display_name),
            ("es", spanish_name),
        ),
    )


MARS_BODY = _planet(
    target="mars barycenter",
    entity_key="mars",
    display_name="Mars",
    spanish_name="Marte",
    physical_body_id="499",
    astronomical_symbol="♂",
)
JUPITER_BODY = _planet(
    target="jupiter barycenter",
    entity_key="jupiter",
    display_name="Jupiter",
    spanish_name="Júpiter",
    physical_body_id="599",
    astronomical_symbol="♃",
)
SATURN_BODY = _planet(
    target="saturn barycenter",
    entity_key="saturn",
    display_name="Saturn",
    spanish_name="Saturno",
    physical_body_id="699",
    astronomical_symbol="♄",
)
URANUS_BODY = _planet(
    target="uranus barycenter",
    entity_key="uranus",
    display_name="Uranus",
    spanish_name="Urano",
    physical_body_id="799",
    astronomical_symbol="♅",
)
NEPTUNE_BODY = _planet(
    target="neptune barycenter",
    entity_key="neptune",
    display_name="Neptune",
    spanish_name="Neptuno",
    physical_body_id="899",
    astronomical_symbol="♆",
)

APPARENT_MAJOR_PLANETS = (
    MARS_BODY,
    JUPITER_BODY,
    SATURN_BODY,
    URANUS_BODY,
    NEPTUNE_BODY,
)

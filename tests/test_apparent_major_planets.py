"""All non-Earth major planets reuse the apparent symbolic-point path."""

from wenu.charts.chart_arguments import _SYMBOLIC_BODY_KEYS
from wenu.charts.detail import ResolvedDetail, SkyContentSelection
from wenu.charts.detail_application import apply_resolved_detail
from wenu.charts.styles import PublicationStyle
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.major_planets import APPARENT_MAJOR_PLANETS
from wenu.sky.mercury import MERCURY_BODY
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_bodies import SYMBOLIC_POINT
from wenu.sky.solar_system_catalog import SOLAR_SYSTEM_BODY_CATALOG


EXPECTED = {
    "mercury": ("mercury", "199", "Mercurio", "☿"),
    "venus": ("venus", "299", "Venus", "♀"),
    "mars": ("mars barycenter", "499", "Marte", "♂"),
    "jupiter": ("jupiter barycenter", "599", "Júpiter", "♃"),
    "saturn": ("saturn barycenter", "699", "Saturno", "♄"),
    "uranus": ("uranus barycenter", "799", "Urano", "♅"),
    "neptune": ("neptune barycenter", "899", "Neptuno", "♆"),
}


def test_catalog_data_separates_provider_targets_from_physical_planet_ids():
    assert set(_SYMBOLIC_BODY_KEYS) == set(EXPECTED)
    assert "earth" not in _SYMBOLIC_BODY_KEYS
    for key, (target, physical_id, spanish_name, symbol) in EXPECTED.items():
        descriptor = SOLAR_SYSTEM_BODY_CATALOG.resolve(key)
        assert descriptor.target == target
        assert descriptor.physical_body_id == physical_id
        assert descriptor.body_class == "planet"
        assert descriptor.supports(SYMBOLIC_POINT)
        assert descriptor.display_name_for("es") == spanish_name
        assert descriptor.astronomical_symbol == symbol
    assert MERCURY_BODY not in APPARENT_MAJOR_PLANETS


def test_every_planet_uses_one_generic_layer_style_and_semantic_path():
    sky = CelestialSphere(None)
    layers = tuple(
        sky.add_solar_system_body(SOLAR_SYSTEM_BODY_CATALOG.resolve(key))
        for key in EXPECTED
    )
    selected = apply_resolved_detail(
        sky,
        ResolvedDetail(
            enabled_layers=set(EXPECTED),
            content_selection=SkyContentSelection(
                solar_system_objects=set(EXPECTED)
            ),
        ),
        base_layer_options=PublicationStyle().layer_options(sky),
    )
    for layer in layers:
        key = layer.body_descriptor.entity_key
        options = selected.layer_options[layer]
        assert options["enabled"] is True
        assert options["geometry"]["selected"] == set(EXPECTED)
        assert options["render"]["style"]["marker"] == "o"
        assert options["render"]["style"]["s"] == 10.5
        identity = semantic_layer_identity(layer)
        assert identity.semantic_path_text == (
            f"sky/solar_system/planets/{key}"
        )
        assert identity.display_name == layer.body_descriptor.display_name

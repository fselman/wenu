"""First drawable Moon symbolic-point contracts."""

from types import SimpleNamespace

from wenu.charts.detail import ResolvedDetail, SkyContentSelection
from wenu.charts.detail_application import apply_resolved_detail
from wenu.charts.styles import PublicationStyle
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.moon import MOON_POINT, MoonLayer
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_points import SolarSystemPointLayer


def test_moon_is_a_thin_shared_point_specialization():
    layer = MoonLayer()

    assert isinstance(layer, SolarSystemPointLayer)
    assert layer.descriptor is MOON_POINT
    assert MOON_POINT.target == "moon"
    assert MOON_POINT.centre == "solar system barycenter"
    assert MOON_POINT.entity_key == "moon"
    assert MOON_POINT.display_name == "Moon"
    assert MOON_POINT.selection_key == "moon"


def test_moon_owns_stable_natural_satellite_semantics():
    identity = semantic_layer_identity(MoonLayer())

    assert identity.semantic_path == (
        "sky", "solar_system", "natural_satellites", "moon"
    )
    assert identity.display_name == "Moon"


def test_moon_is_default_off_and_style_owns_symbol_and_label():
    sky = CelestialSphere(None)
    layer = sky.add_moon()
    disabled = apply_resolved_detail(sky, ResolvedDetail())
    assert disabled.layer_options[layer]["enabled"] is False

    selected = apply_resolved_detail(
        sky,
        ResolvedDetail(
            enabled_layers={"moon"},
            content_selection=SkyContentSelection(
                solar_system_objects={"moon"}
            ),
        ),
        base_layer_options=PublicationStyle().layer_options(sky),
    )
    options = selected.layer_options[layer]
    assert options["enabled"] is True
    assert options["geometry"]["selected"] == {"moon"}
    assert options["render"]["style"]["marker"] == "o"
    assert options["render"]["style"]["facecolors"] == "none"
    assert options["render"]["draw_labels"] is True


def test_moon_selection_rejects_another_body():
    layer = MoonLayer(
        source_factory=lambda observer: SimpleNamespace()
    )

    try:
        layer.realize(
            object(),
            object(),
            selected={"venus"},
        )
    except ValueError as error:
        assert "Moon selection must contain only moon" in str(error)
    else:
        raise AssertionError("Moon accepted a Venus selection.")

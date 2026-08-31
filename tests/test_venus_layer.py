"""First drawable Venus layer contracts."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu.charts.detail import ResolvedDetail, SkyContentSelection
from wenu.charts.detail_application import apply_resolved_detail
from wenu.charts.styles import PublicationStyle
from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.semantic_identity import semantic_layer_identity
from wenu.sky.solar_system_points import SolarSystemPointLayer
from wenu.sky.venus import VENUS_POINT, VenusLayer


def context():
    observation = ObservationContext(
        longitude_deg=-71.0,
        latitude_deg=-33.0,
        elevation_m=100.0,
        instant="2026-08-30T00:00:00.000",
        time_scale="utc",
    )
    return LayerRealizationContext(
        product_coordinate_spec=CoordinateSpec(
            frame="altaz",
            origin="observer",
            position_status=PositionStatus.APPARENT,
            instant=observation.instant,
            time_scale=observation.time_scale,
        ),
        observation=observation,
        evaluation_instant=observation.instant,
        evaluation_time_scale=observation.time_scale,
    )


def test_venus_uses_one_accepted_chain_and_one_product_transform():
    calls = []
    source = SimpleNamespace(
        resource=SimpleNamespace(sha256="a" * 64)
    )
    observer_state = object()
    astrometric = object()
    apparent = SimpleNamespace(
        geometry=SphericalPoints(
            np.asarray((198.0,)),
            np.asarray((-11.0,)),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="observer",
                position_status=PositionStatus.APPARENT,
                instant="2026-08-30T00:00:00.000",
                time_scale="utc",
                provenance=("accepted apparent Venus",),
            ),
        )
    )
    transformed = object()

    class Astrometric:
        def direction(self, actual_source, request, actual_state):
            calls.append(("astrometric", request))
            assert actual_source is source
            assert actual_state is observer_state
            assert request.target == "venus"
            assert request.centre == "solar system barycenter"
            return astrometric

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            calls.append(("apparent", observer))
            assert value is astrometric
            assert policy is VENUS_POINT.correction_policy
            return apparent

    class Coordinates:
        def transform(self, geometry, target, observation):
            calls.append(("transform", geometry))
            assert target is realization.product_coordinate_spec
            assert observation is realization.observation
            assert geometry.labels.tolist() == ["Venus"]
            assert geometry.metadata["ephemeris_sha256"] == "a" * 64
            return transformed

    realization = context()
    observer = object()
    layer = VenusLayer(
        source_factory=lambda value: source,
        observer_state_factory=lambda value, *, source: observer_state,
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )

    assert layer.realize(realization, observer) is transformed
    assert [name for name, _ in calls] == [
        "astrometric", "apparent", "transform"
    ]


def test_venus_is_a_thin_shared_point_specialization():
    layer = VenusLayer()
    assert isinstance(layer, SolarSystemPointLayer)
    assert layer.descriptor is VENUS_POINT


def test_venus_requires_the_typed_context_and_never_uses_legacy_geometry():
    layer = VenusLayer()
    with pytest.raises(TypeError, match="typed LayerRealizationContext"):
        layer.spherical_geometry(object())
    with pytest.raises(TypeError, match="LayerRealizationContext"):
        layer.realize(object(), object())


def test_venus_owns_the_stable_solar_system_semantic_path():
    identity = semantic_layer_identity(VenusLayer())
    assert identity.semantic_path == (
        "sky", "solar_system", "planets", "venus"
    )
    assert identity.display_name == "Venus"


def test_venus_is_default_off_and_style_owns_symbol_and_label():
    sky = CelestialSphere(None)
    layer = sky.add_venus()
    disabled = apply_resolved_detail(sky, ResolvedDetail())
    assert disabled.layer_options[layer]["enabled"] is False

    selected = apply_resolved_detail(
        sky,
        ResolvedDetail(
            enabled_layers={"venus"},
            content_selection=SkyContentSelection(
                solar_system_objects={"venus"}
            ),
        ),
        base_layer_options=PublicationStyle().layer_options(sky),
    )
    options = selected.layer_options[layer]
    assert options["enabled"] is True
    assert options["geometry"]["selected"] == {"venus"}
    assert options["render"]["style"]["marker"] == "o"
    assert options["render"]["draw_labels"] is True

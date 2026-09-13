"""Shared symbolic Solar-System point-layer contracts."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor
from wenu.sky.solar_system_points import (
    EphemerisSourceBinding,
    SolarSystemPointDescriptor,
    SolarSystemPointLayer,
    _provider_gas_tail_position_angle,
)
from wenu.solar_system_directions import ApparentCorrectionPolicy


def context():
    observation = ObservationContext(
        longitude_deg=-71.0,
        latitude_deg=-33.0,
        elevation_m=52.0,
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


def test_descriptor_freezes_body_identity_centre_and_correction_policy():
    descriptor = SolarSystemPointDescriptor(
        target="moon",
        entity_key="moon",
        display_name="Moon",
        selection_key="moon",
    )

    assert descriptor.target == "moon"
    assert descriptor.entity_key == "moon"
    assert descriptor.display_name == "Moon"
    assert descriptor.selection_key == "moon"
    assert descriptor.centre == "solar system barycenter"
    assert isinstance(
        descriptor.correction_policy,
        ApparentCorrectionPolicy,
    )
    with pytest.raises(AttributeError):
        descriptor.target = "venus"


@pytest.mark.parametrize(
    ("field", "value", "error"),
    (
        ("target", "", ValueError),
        ("entity_key", 301, TypeError),
        ("display_name", " ", ValueError),
        ("selection_key", None, TypeError),
        ("centre", "", ValueError),
    ),
)
def test_descriptor_rejects_missing_or_untyped_identity(field, value, error):
    values = {
        "target": "moon",
        "entity_key": "moon",
        "display_name": "Moon",
        "selection_key": "moon",
        "centre": "solar system barycenter",
    }
    values[field] = value
    with pytest.raises(error):
        SolarSystemPointDescriptor(**values)


def test_shared_layer_realizes_a_body_without_projection_or_rendering():
    descriptor = SolarSystemBodyDescriptor(
        target="venus",
        entity_key="venus",
        display_name="Venus",
        selection_key="venus",
        astronomical_symbol="♀",
    )
    calls = []
    source = SimpleNamespace(
        resource=SimpleNamespace(sha256="b" * 64)
    )
    observer_state = object()
    astrometric = object()
    apparent = SimpleNamespace(
        geometry=SphericalPoints(
            np.asarray((358.0,)),
            np.asarray((2.0,)),
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
            calls.append("astrometric")
            assert actual_source is source
            assert actual_state is observer_state
            assert request.target == "venus"
            assert request.centre == "solar system barycenter"
            return astrometric

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            calls.append("apparent")
            assert value is astrometric
            assert policy is descriptor.correction_policy
            return apparent

    class Coordinates:
        def transform(self, geometry, target, observation):
            calls.append("transform")
            assert geometry.ids.tolist() == ["venus"]
            assert geometry.labels.tolist() == ["♀"]
            assert geometry.names.tolist() == ["Venus"]
            assert geometry.metadata["semantic_entity_keys"].tolist() == [
                "venus"
            ]
            assert geometry.metadata[
                "semantic_entity_display_names"
            ].tolist() == ["Venus"]
            assert geometry.metadata["ephemeris_sha256"] == "b" * 64
            assert geometry.metadata["apparent_provenance"] == (
                "accepted apparent Venus",
            )
            assert target is realization.product_coordinate_spec
            assert observation is realization.observation
            return transformed

    realization = context()
    observer = object()
    layer = SolarSystemPointLayer(
        descriptor,
        source_factory=lambda value: source,
        observer_state_factory=lambda value, *, source: observer_state,
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )

    assert layer.realize(
        realization,
        observer,
        selected={"mercury", "venus"},
    ) is transformed
    assert calls == ["astrometric", "apparent", "transform"]


def test_shared_layer_validates_selection_context_and_geometry_options():
    descriptor = SolarSystemPointDescriptor(
        target="moon",
        entity_key="moon",
        display_name="Moon",
        selection_key="moon",
    )
    layer = SolarSystemPointLayer(descriptor)

    with pytest.raises(TypeError, match="typed LayerRealizationContext"):
        layer.spherical_geometry(object())
    with pytest.raises(TypeError, match="LayerRealizationContext"):
        layer.realize(object(), object())
    with pytest.raises(ValueError, match="contain moon"):
        layer.realize(context(), object(), selected={"venus"})
    with pytest.raises(TypeError, match="accepts no geometry options"):
        layer.realize(context(), object(), unexpected=True)


def test_shared_layer_accepts_distinct_target_and_observer_sources():
    descriptor = SolarSystemBodyDescriptor(
        target="ceres",
        entity_key="ceres",
        display_name="Ceres",
        selection_key="ceres",
        canonical_designation="(1) Ceres",
    )
    target_source = SimpleNamespace(
        resource=SimpleNamespace(primary=SimpleNamespace(sha256="c" * 64))
    )
    observer_source = SimpleNamespace(resource=object())
    astrometric = object()
    apparent = SimpleNamespace(
        geometry=SphericalPoints(
            np.asarray((10.0,)),
            np.asarray((20.0,)),
            coordinate_spec=CoordinateSpec(
                frame="icrs", origin="observer",
                position_status=PositionStatus.APPARENT,
            ),
        )
    )

    class Astrometric:
        def direction(self, source, request, observer_state):
            assert source is target_source
            assert observer_state == "observer-state"
            return astrometric

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            assert value is astrometric
            assert source is observer_source
            return apparent

    class Coordinates:
        def transform(self, geometry, target, observation):
            assert geometry.labels.tolist() == ["(1) Ceres"]
            assert geometry.metadata["ephemeris_sha256"] == "c" * 64
            return geometry

    layer = SolarSystemPointLayer(
        descriptor,
        source_resolver=lambda body, observer: EphemerisSourceBinding(
            target_source, observer_source
        ),
        observer_state_factory=lambda observer, *, source: (
            "observer-state" if source is observer_source else None
        ),
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )
    result = layer.realize(context(), object(), selected={"ceres"})
    assert result.labels.tolist() == ["(1) Ceres"]


def test_comet_layer_realizes_simultaneous_sun_and_tail_reference():
    descriptor = SolarSystemBodyDescriptor(
        target="2p",
        entity_key="comet_2p",
        display_name="2P/Encke",
        selection_key="2p",
        body_class="comet",
        canonical_designation="2P/Encke",
        iau_number=2,
    )
    target_source = SimpleNamespace(
        resource=SimpleNamespace(primary=SimpleNamespace(sha256="d" * 64))
    )
    observer_source = object()
    coordinate_spec = CoordinateSpec(
        frame="icrs", origin="observer",
        position_status=PositionStatus.APPARENT,
        provenance=("test apparent",),
    )

    class Astrometric:
        def direction(self, source, request, observer_state):
            assert observer_state == "observer-state"
            if request.target == "sun":
                assert source is observer_source
            else:
                assert source is target_source
            return request.target

    class Apparent:
        def direction(self, value, *, observer, source, policy):
            del observer, policy
            assert source is observer_source
            coordinates = {
                "2p": (347.16284728400217, 11.5633172622082),
                "sun": (227.79603677620744, -17.8009756969018),
            }[value]
            return SimpleNamespace(
                geometry=SphericalPoints(
                    [coordinates[0]], [coordinates[1]],
                    coordinate_spec=coordinate_spec,
                )
            )

    class Coordinates:
        def transform(self, geometry, target, observation):
            del target, observation
            return geometry

    layer = SolarSystemPointLayer(
        descriptor,
        source_resolver=lambda body, observer: EphemerisSourceBinding(
            target_source, observer_source
        ),
        observer_state_factory=lambda observer, *, source: "observer-state",
        astrometric_realizer=Astrometric(),
        apparent_realizer=Apparent(),
        coordinate_service=Coordinates(),
    )

    result = layer.realize(context(), object(), selected={"2p"})

    assert len(result) == 2
    assert result.ids.tolist() == [
        "comet_2p", "comet_2p__antisolar_reference",
    ]
    assert result.labels.tolist() == ["2P/Encke", None]
    assert result.metadata["comet_symbol_orientation_reference_index"] == 1
    assert result.metadata["antisolar_position_angle_deg"] == pytest.approx(
        76.06332619563693
    )
    assert result.metadata["comet_tail_orientation_source"] == (
        "Wenu apparent Sun-comet fallback"
    )


def test_provider_psang_is_typed_and_has_precedence_contract():
    class Source:
        def apparent_gas_tail_position_angle_deg(
            self, *, request, observer_state
        ):
            assert request == "request"
            assert observer_state == "observer-state"
            return 248.649

    assert _provider_gas_tail_position_angle(
        Source(), "request", "observer-state"
    ) == pytest.approx(248.649)
    assert _provider_gas_tail_position_angle(
        object(), "request", "observer-state"
    ) is None

    class InvalidSource:
        def apparent_gas_tail_position_angle_deg(self, **kwargs):
            del kwargs
            return 360.0

    with pytest.raises(ValueError, match=r"\[0, 360\)"):
        _provider_gas_tail_position_angle(
            InvalidSource(), "request", "observer-state"
        )

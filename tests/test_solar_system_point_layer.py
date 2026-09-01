"""Shared symbolic Solar-System point-layer contracts."""

from types import SimpleNamespace

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, ObservationContext, PositionStatus
from wenu.geometry.spherical import SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_points import (
    SolarSystemPointDescriptor,
    SolarSystemPointLayer,
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
    descriptor = SolarSystemPointDescriptor(
        target="moon",
        entity_key="moon",
        display_name="Moon",
        selection_key="moon",
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
                provenance=("accepted apparent Moon",),
            ),
        )
    )
    transformed = object()

    class Astrometric:
        def direction(self, actual_source, request, actual_state):
            calls.append("astrometric")
            assert actual_source is source
            assert actual_state is observer_state
            assert request.target == "moon"
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
            assert geometry.ids.tolist() == ["moon"]
            assert geometry.labels.tolist() == ["Moon"]
            assert geometry.names.tolist() == ["Moon"]
            assert geometry.metadata["semantic_entity_keys"].tolist() == [
                "moon"
            ]
            assert geometry.metadata[
                "semantic_entity_display_names"
            ].tolist() == ["Moon"]
            assert geometry.metadata["ephemeris_sha256"] == "b" * 64
            assert geometry.metadata["apparent_provenance"] == (
                "accepted apparent Moon",
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
        selected={"moon", "venus"},
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

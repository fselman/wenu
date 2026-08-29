"""Minimal layer-realization context and controlled-provider contracts."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from wenu.coordinate_service import CoordinateService
from wenu.coordinates import (
    CoordinateSpec,
    ObservationContext,
    PositionStatus,
)
from wenu.geometry.spherical import SphericalPoints
from wenu.positions import PositionProvider
from wenu.sky.celestial_sphere import CelestialSphere
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.sky_layer import SkyLayer


class IdentityProjection:
    def project_geometry(self, geometry):
        return geometry


class RecordingRenderer:
    def __init__(self):
        self.drawn = []

    def draw(self, geometry, **options):
        self.drawn.append((geometry, options))
        return (object(),)


class LegacyLayer(SkyLayer):
    layer_name = "legacy"

    def __init__(self):
        self.calls = []

    def spherical_geometry(self, observer, **options):
        self.calls.append((observer, options))
        return SphericalPoints(
            lon_deg=np.asarray([1.0]),
            lat_deg=np.asarray([2.0]),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                provider="legacy test layer",
            ),
        )


class ControlledProvider:
    def __init__(self):
        self.instants = []

    def position(self, instant=None):
        self.instants.append(instant)
        return SphericalPoints(
            lon_deg=np.asarray([10.0]),
            lat_deg=np.asarray([20.0]),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="solar-system-barycenter",
                position_status=PositionStatus.GEOMETRIC,
                instant=instant,
                time_scale="tt",
                provider="controlled test provider",
                provenance=("deterministic test state",),
            ),
            ids=np.asarray(["controlled-body"], dtype=object),
        )


class ControlledDynamicLayer(SkyLayer):
    layer_name = "controlled_dynamic"

    def __init__(self, provider):
        self.provider = provider
        self.realizations = []

    def spherical_geometry(self, observer, **options):
        raise AssertionError(
            "explicit dynamic realization must not use the legacy call"
        )

    def realize(self, context, observer, **geometry_options):
        self.realizations.append(
            (context, observer, dict(geometry_options))
        )
        native = self.provider.position(context.evaluation_instant)
        return CoordinateService().transform(
            native,
            context.product_coordinate_spec,
            observation=context.observation,
        )


def _context():
    instant = "2026-08-29T21:00:00"
    return LayerRealizationContext(
        product_coordinate_spec=CoordinateSpec(
            frame="galactic",
            origin="galactic-center",
            position_status=PositionStatus.GEOMETRIC,
            instant=instant,
            time_scale="tt",
            provider="controlled test provider",
            provenance=("deterministic test state",),
        ),
        observation=ObservationContext(
            longitude_deg=-71.0,
            latitude_deg=-32.0,
            elevation_m=100.0,
            instant=instant,
            time_scale="tt",
        ),
        evaluation_instant=instant,
        evaluation_time_scale="TT",
        reference_equinox="J2000.0",
    )


def _draw(sphere, *, observer, realization_context=None, layer_options=None):
    return sphere.draw_chart(
        projection=IdentityProjection(),
        renderer=RecordingRenderer(),
        observer=observer,
        realization_context=realization_context,
        layer_options=layer_options,
    )


def test_realization_context_is_immutable_and_normalized():
    context = _context()

    assert context.evaluation_time_scale == "tt"
    assert context.reference_equinox == "J2000.0"
    with pytest.raises(FrozenInstanceError):
        context.evaluation_instant = "later"


@pytest.mark.parametrize(
    ("values", "error", "message"),
    [
        (
            {"product_coordinate_spec": object()},
            TypeError,
            "product_coordinate_spec",
        ),
        (
            {
                "product_coordinate_spec": CoordinateSpec(
                    frame="icrs",
                    origin="solar-system-barycenter",
                ),
                "observation": object(),
            },
            TypeError,
            "observation",
        ),
        (
            {
                "product_coordinate_spec": CoordinateSpec(
                    frame="icrs",
                    origin="solar-system-barycenter",
                ),
                "evaluation_instant": "2026-08-29T21:00:00",
            },
            ValueError,
            "supplied together",
        ),
    ],
)
def test_realization_context_rejects_incomplete_scientific_identity(
    values, error, message,
):
    with pytest.raises(error, match=message):
        LayerRealizationContext(**values)


def test_draw_chart_without_context_keeps_the_exact_legacy_layer_call():
    observer = object()
    layer = LegacyLayer()
    sphere = CelestialSphere(None)
    sphere.add(layer)

    result = _draw(
        sphere,
        observer=observer,
        layer_options={"legacy": {"geometry": {"sample": 7}}},
    )

    assert layer.calls == [(observer, {"sample": 7})]
    assert result.layers[0].spherical.lon_deg.tolist() == [1.0]


def test_default_realization_adapter_preserves_unmigrated_layers():
    observer = object()
    context = _context()
    layer = LegacyLayer()
    sphere = CelestialSphere(None)
    sphere.add(layer)

    result = _draw(
        sphere,
        observer=observer,
        realization_context=context,
        layer_options={"legacy": {"geometry": {"sample": 11}}},
    )

    assert layer.calls == [(observer, {"sample": 11})]
    assert result.layers[0].spherical.coordinate_spec.frame == "icrs"


def test_controlled_provider_enters_before_projection_through_service():
    observer = object()
    context = _context()
    provider = ControlledProvider()
    layer = ControlledDynamicLayer(provider)
    sphere = CelestialSphere(None)
    sphere.add(layer)

    result = _draw(
        sphere,
        observer=observer,
        realization_context=context,
        layer_options={
            "controlled_dynamic": {"geometry": {"selected": "body"}}
        },
    )

    assert isinstance(provider, PositionProvider)
    assert provider.instants == [context.evaluation_instant]
    assert layer.realizations == [
        (context, observer, {"selected": "body"})
    ]
    spherical = result.layers[0].spherical
    assert spherical.coordinate_spec == context.product_coordinate_spec
    assert spherical.ids.tolist() == ["controlled-body"]
    assert np.isfinite(spherical.lon_deg).all()
    assert np.isfinite(spherical.lat_deg).all()


def test_draw_chart_rejects_an_untyped_realization_context():
    sphere = CelestialSphere(None)
    sphere.add(LegacyLayer())

    with pytest.raises(TypeError, match="LayerRealizationContext"):
        _draw(
            sphere,
            observer=object(),
            realization_context=object(),
        )

"""Scientific contract tests for sampled Solar-System trajectories."""

from dataclasses import FrozenInstanceError
from math import cos, radians, sin
from types import SimpleNamespace

import numpy as np
import pytest
from astropy.time import Time

from wenu.coordinates import (
    CoordinateSpec,
    ObservationContext,
    PositionStatus,
)
from wenu.ephemeris import EphemerisResourceIdentity, EphemerisState
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.solar_system_points import SolarSystemPointDescriptor
from wenu.sky.solar_system_tracks import (
    SolarSystemTrackRealizer,
    SolarSystemTrackRequest,
)
from wenu.solar_system_directions import (
    ApparentDirection,
    ObserverBarycentricState,
)

RESOURCE = EphemerisResourceIdentity(
    provider="test/JPL",
    model="track-test",
    filename="track.bsp",
    sha256="b" * 64,
    coverage_start="JD 2400000.5",
    coverage_end="JD 2500000.5",
    coverage_time_scale="tdb",
)
DESCRIPTOR = SolarSystemPointDescriptor(
    target="venus",
    entity_key="venus",
    display_name="Venus",
    selection_key="venus",
)
PRODUCT_SPEC = CoordinateSpec(
    frame="icrs",
    origin="observer",
    position_status=PositionStatus.APPARENT,
    provider="test product",
)
OBSERVATION = ObservationContext(
    longitude_deg=-71.230289,
    latitude_deg=-32.443342,
    elevation_m=52.0,
    instant="2026-08-30T00:00:00.000",
    time_scale="utc",
)
CONTEXT = LayerRealizationContext(
    product_coordinate_spec=PRODUCT_SPEC,
    observation=OBSERVATION,
)


class TrackSource:
    resource = RESOURCE

    def __init__(self):
        self.requests = []

    def state(self, request):
        self.requests.append(request)
        offset = float(
            (
                Time(request.instant, scale=request.time_scale)
                - Time("2026-08-30T00:00:00", scale="utc")
            ).to_value("day")
        )
        angle = radians(offset)
        return EphemerisState(
            request=request,
            position=(cos(angle), sin(angle), 0.1),
            velocity=(0.0, 0.0, 0.0),
            position_unit="au",
            velocity_unit="au/day",
            resource=RESOURCE,
            provider_target_id="299",
            provider_centre_id="0",
        )


class ApparentRealizer:
    def __init__(self):
        self.receptions = []

    def direction(self, astrometric, *, observer, source, policy):
        del observer, source
        self.receptions.append(astrometric.request.reception_instant)
        native = astrometric.geometry
        geometry = SphericalPoints(
            native.lon_deg.copy(),
            native.lat_deg.copy(),
            coordinate_spec=CoordinateSpec(
                frame="icrs",
                origin="observer",
                position_status=PositionStatus.APPARENT,
                instant=astrometric.request.reception_instant,
                time_scale=astrometric.request.reception_time_scale,
                provider=RESOURCE.provider,
                model=policy.model,
                provenance=("deterministic apparent direction",),
                corrections=frozenset(
                    (
                        "one-way-light-time",
                        "aberration",
                        "gravitational-deflection",
                    )
                ),
            ),
            ids=np.asarray(("venus",), dtype=object),
        )
        return ApparentDirection(
            astrometric=astrometric,
            policy=policy,
            geometry=geometry,
        )


def observer_state(sample_observer, *, source):
    instant = sample_observer.t_astropy
    return ObserverBarycentricState(
        observer_id="La Ligua",
        centre="solar system barycenter",
        frame="icrf",
        instant=instant.isot,
        time_scale=instant.scale,
        position=(0.0, 0.0, 0.0),
        velocity=(0.0, 0.0, 0.0),
        position_unit="au",
        velocity_unit="au/day",
        resource=source.resource,
        provider_observer_id="WGS84 site",
        provider_centre_id="0",
    )


def sample_observer(observer, instant):
    del observer
    return SimpleNamespace(t_astropy=instant)


def request(**overrides):
    values = {
        "descriptor": DESCRIPTOR,
        "start_instant": "2026-08-30T00:00:00Z",
        "start_time_scale": "utc",
        "sample_step_days": 0.4,
        "tick_step_days": 0.75,
        "tick_count": 2,
    }
    values.update(overrides)
    return SolarSystemTrackRequest(**values)


def test_request_is_frozen_and_inserts_exact_tick_instants():
    value = request()

    assert value.start_instant == "2026-08-30T00:00:00.000000000"
    assert value.duration_days == pytest.approx(1.5)
    assert value.sample_offsets_days == pytest.approx(
        (0.0, 0.4, 0.75, 0.8, 1.2, 1.5)
    )
    assert value.tick_offsets_days == pytest.approx((0.0, 0.75, 1.5))
    with pytest.raises(FrozenInstanceError):
        value.tick_count = 3


@pytest.mark.parametrize(
    ("name", "value", "error"),
    (
        ("sample_step_days", 0.0, ValueError),
        ("tick_step_days", float("nan"), ValueError),
        ("tick_count", 0, ValueError),
        ("tick_count", True, TypeError),
        ("start_time_scale", "", ValueError),
    ),
)
def test_request_rejects_invalid_time_sampling(name, value, error):
    with pytest.raises(error):
        request(**{name: value})


def test_realizer_assembles_one_curve_and_transforms_only_after_sampling():
    source = TrackSource()
    apparent = ApparentRealizer()
    calls = []

    class CoordinateService:
        def transform(self, geometry, target_spec, observation):
            calls.append((geometry, target_spec, observation))
            return SphericalCurves(
                lon_deg=tuple(value.copy() for value in geometry.lon_deg),
                lat_deg=tuple(value.copy() for value in geometry.lat_deg),
                coordinate_spec=target_spec,
                closed=geometry.closed.copy(),
                ids=geometry.ids.copy(),
                labels=geometry.labels.copy(),
                names=geometry.names.copy(),
                metadata=dict(geometry.metadata),
            )

    result = SolarSystemTrackRealizer(
        source_factory=lambda observer: source,
        sample_observer_factory=sample_observer,
        observer_state_factory=observer_state,
        apparent_realizer=apparent,
        coordinate_service=CoordinateService(),
    ).curve(
        request(),
        context=CONTEXT,
        observer=object(),
    )

    assert len(calls) == 1
    native, target_spec, observation = calls[0]
    assert isinstance(native, SphericalCurves)
    assert native.coordinate_spec.frame == "icrs"
    assert native.coordinate_spec.position_status is PositionStatus.APPARENT
    assert native.coordinate_spec.instant is None
    assert target_spec is PRODUCT_SPEC
    assert observation is OBSERVATION

    assert result.geometry.coordinate_spec is PRODUCT_SPEC
    assert result.geometry.ids.tolist() == ["venus.track"]
    assert result.geometry.names.tolist() == ["Venus"]
    assert len(result.geometry.lon_deg[0]) == 6
    assert result.tick_sample_indices == (0, 2, 5)
    assert result.sample_instants[0] == "2026-08-30T00:00:00.000000000"
    assert result.sample_instants[-1] == "2026-08-31T12:00:00.000000000"
    assert result.sample_time_scale == "utc"
    assert len(result.apparent_directions) == 6
    assert len(apparent.receptions) == 6
    assert result.geometry.metadata["ephemeris_sha256"] == "b" * 64
    assert result.geometry.metadata["tick_offsets_days"] == pytest.approx(
        (0.0, 0.75, 1.5)
    )
    assert "chart product frame held fixed" in result.provenance[-1]


def test_realizer_uses_one_source_and_reevaluates_observer_for_each_sample():
    source = TrackSource()
    source_calls = []
    observer_instants = []

    def source_factory(observer):
        source_calls.append(observer)
        return source

    def state_factory(sample, *, source):
        observer_instants.append(sample.t_astropy.isot)
        return observer_state(sample, source=source)

    result = SolarSystemTrackRealizer(
        source_factory=source_factory,
        sample_observer_factory=sample_observer,
        observer_state_factory=state_factory,
        apparent_realizer=ApparentRealizer(),
    ).curve(
        request(
            sample_step_days=0.75,
            tick_step_days=0.75,
            tick_count=2,
        ),
        context=CONTEXT,
        observer="base observer",
    )

    assert source_calls == ["base observer"]
    assert observer_instants == list(result.sample_instants)
    assert len(observer_instants) == 3
    assert all(
        direction.astrometric.observer_state.instant == instant
        for direction, instant in zip(
            result.apparent_directions,
            result.sample_instants,
        )
    )


def test_realizer_requires_typed_context_with_observation():
    realizer = SolarSystemTrackRealizer()

    with pytest.raises(TypeError, match="LayerRealizationContext"):
        realizer.curve(request(), context=object(), observer=object())

    without_observation = LayerRealizationContext(
        product_coordinate_spec=PRODUCT_SPEC,
    )
    with pytest.raises(ValueError, match="observation context"):
        realizer.curve(
            request(),
            context=without_observation,
            observer=object(),
        )

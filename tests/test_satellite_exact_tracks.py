"""Exact local satellite track evidence and output-neutral layer tests."""

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from math import cos, radians, sin

import numpy as np
import pytest

from wenu.coordinates import CoordinateSpec, PositionStatus
from wenu.geometry.spherical import SphericalCurves, SphericalPoints
from wenu.satellite_crossings import (
    InclusiveTimeInterval,
    SatelliteCrossingCandidate,
    SatelliteCrossingResult,
    SatelliteFieldOfView,
    SatelliteIdentity,
    SatelliteObserver,
)
from wenu.satellites import load_snapshot
from wenu.satellites.exact_tracks import (
    EXACT_LOCAL_TRACK_STATUS,
    ExactLocalSatelliteTrackRealizer,
    ExactLocalTrackError,
    ExactLocalTrackEvaluation,
    ExactLocalTrackPolicy,
    _realize_track,
)
from wenu.sky.realization import LayerRealizationContext
from wenu.sky.satellite_exact_track_layer import (
    SatelliteExactTrackEventsLayer,
    SatelliteExactTrackLayer,
)
from wenu.sky.semantic_identity import semantic_layer_identity


START = datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc)


def iso(value):
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def instant(seconds):
    return START + timedelta(seconds=seconds)


def crossing(
    *,
    entry=0.0,
    closest=2.0,
    exit_=4.0,
    identifier=900001,
    snapshot_sha256="a" * 64,
    field_id="field-one",
    orbit_solution_id="orbit-one",
    element_epoch=None,
    identity=None,
):
    observer = SatelliteObserver(
        "la-ligua",
        -71.230289,
        -32.443342,
        52.0,
        refraction_policy="vacuum",
        earth_orientation_policy="iers-a-bundled",
    )
    spec = CoordinateSpec(
        frame="gcrs-axes",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        instant=iso(START),
        time_scale="utc",
        provider="exact crossing test",
    )
    field = SatelliteFieldOfView(
        field_id,
        0.0,
        0.0,
        20.0,
        spec,
    )
    candidate = SatelliteCrossingCandidate(
        identity or SatelliteIdentity(identifier, "TEST SAT", "2026-001A", "U"),
        observer,
        field,
        InclusiveTimeInterval(iso(START), iso(instant(10.0))),
        "wenu local crossing oracle",
        orbit_solution_id=orbit_solution_id,
        snapshot_sha256=snapshot_sha256,
        element_epoch=iso(START) if element_epoch is None else element_epoch,
        provenance=("accepted exact crossing",),
    )
    return SatelliteCrossingResult(
        candidate,
        iso(instant(entry)),
        iso(instant(exit_)),
        iso(instant(closest)),
        1.0,
        range_km=500.0,
        angular_rate_deg_per_s=1.0,
        provenance=("accepted event solution",),
    )


def longitude_evaluator(counter=None, *, curve=lambda seconds: seconds):
    def evaluate(instant_utc):
        if counter is not None:
            counter.append(instant_utc)
        value = datetime.fromisoformat(instant_utc.replace("Z", "+00:00"))
        seconds = (value - START).total_seconds()
        longitude = radians(curve(seconds))
        return ExactLocalTrackEvaluation(
            instant_utc,
            (cos(longitude), sin(longitude), 0.0),
            500.0 + seconds,
            provenance=("deterministic fake evaluator",),
        )

    return evaluate


def policy(**values):
    defaults = {
        "angular_chord_tolerance_deg": 0.01,
        "maximum_step_seconds": 1.0,
        "max_depth": 16,
        "max_evaluations": 100,
        "max_samples": 100,
    }
    defaults.update(values)
    return ExactLocalTrackPolicy(**defaults)


def track(**policy_values):
    return _realize_track(
        crossing(),
        policy(**policy_values),
        longitude_evaluator(),
        provenance=("synthetic exact-track test",),
    )


def test_exact_event_anchors_partition_deterministic_sampling_and_cache():
    calls = []
    value = _realize_track(
        crossing(),
        policy(),
        longitude_evaluator(calls),
        provenance=("synthetic exact-track test",),
    )

    assert tuple(item.instant_utc for item in value.samples) == tuple(
        iso(instant(seconds)) for seconds in (0, 1, 2, 3, 4)
    )
    assert value.samples[0].roles == ("entry",)
    assert value.samples[2].roles == ("closest_approach",)
    assert value.samples[-1].roles == ("exit",)
    assert len(calls) == len(set(calls))
    assert all(
        value.crossing.entry_instant
        <= item
        <= value.crossing.exit_instant
        for item in calls
    )
    assert value.sample_time_scale == "utc"
    assert value.coordinate_spec.frame == "gcrs-axes"
    assert value.coordinate_spec.instant is None
    assert value.coordinate_spec.time_scale is None


def test_curvature_midpoint_rule_subdivides_below_maximum_step():
    value = _realize_track(
        crossing(entry=0.0, closest=1.0, exit_=2.0),
        policy(
            angular_chord_tolerance_deg=0.01,
            maximum_step_seconds=10.0,
        ),
        longitude_evaluator(curve=lambda seconds: 5.0 * seconds * seconds),
    )

    assert len(value.samples) > 3
    assert value.samples[0].instant_utc == iso(instant(0.0))
    assert value.samples[-1].instant_utc == iso(instant(2.0))


def test_coincident_events_are_one_sample_with_all_roles():
    value = _realize_track(
        crossing(entry=2.0, closest=2.0, exit_=2.0),
        policy(),
        longitude_evaluator(),
    )

    assert len(value.samples) == 1
    assert value.samples[0].roles == (
        "entry",
        "closest_approach",
        "exit",
    )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"maximum_step_seconds": 0.1, "max_depth": 1}, "depth"),
        ({"maximum_step_seconds": 0.1, "max_evaluations": 3}, "evaluation limit"),
        ({"maximum_step_seconds": 1.0, "max_samples": 2}, "sample limit"),
    ],
)
def test_limits_fail_closed_without_partial_evidence(overrides, message):
    with pytest.raises(ExactLocalTrackError, match=message):
        _realize_track(
            crossing(),
            policy(**overrides),
            longitude_evaluator(),
        )


def test_evaluation_failure_is_typed_and_names_the_failed_instant():
    def fail(instant_utc):
        raise ValueError("synthetic propagation failure")

    with pytest.raises(ExactLocalTrackError, match="track evaluation failed"):
        _realize_track(crossing(), policy(), fail)


def test_track_identity_is_repeatable_and_binds_policy_crossing_and_samples():
    one = track()
    same = track()
    changed_policy = track(angular_chord_tolerance_deg=0.02)
    changed_crossing = _realize_track(
        crossing(field_id="field-two"),
        policy(),
        longitude_evaluator(),
    )
    changed_samples = _realize_track(
        crossing(),
        policy(),
        longitude_evaluator(curve=lambda seconds: seconds + 0.01 * seconds * seconds),
    )

    assert one == same
    assert one.track_identity_sha256 == same.track_identity_sha256
    assert len(one.track_identity_sha256) == 64
    assert len(
        {
            one.track_identity_sha256,
            changed_policy.track_identity_sha256,
            changed_crossing.track_identity_sha256,
            changed_samples.track_identity_sha256,
        }
    ) == 4


def test_output_neutral_track_and_event_views_reuse_retained_samples():
    value = track()
    context = LayerRealizationContext(value.coordinate_spec)
    path_layer = SatelliteExactTrackLayer(value)
    event_layer = SatelliteExactTrackEventsLayer(value)

    path = path_layer.realize(context, observer=None)
    events = event_layer.realize(context, observer=None)

    assert isinstance(path, SphericalCurves)
    assert len(path) == 1
    assert not path.closed[0]
    np.testing.assert_allclose(
        path.lon_deg[0],
        [item.longitude_deg for item in value.samples],
    )
    assert path.metadata["scientific_status"] == EXACT_LOCAL_TRACK_STATUS
    assert path.metadata["exact_crossing_events"] is True
    assert path.metadata["global_continuous_error_proven"] is False
    assert path.metadata["sample_time_scale"] == "utc"
    assert isinstance(events, SphericalPoints)
    assert tuple(events.metadata["event_roles"]) == (
        "entry",
        "closest_approach",
        "exit",
    )
    assert events.metadata["recomputed"] is False
    expected = {
        role: sample.longitude_deg
        for sample in value.samples
        for role in sample.roles
    }
    assert tuple(events.lon_deg) == pytest.approx(
        tuple(expected[role] for role in events.metadata["event_roles"])
    )


def test_singleton_layer_is_a_point_and_never_an_invented_segment():
    value = _realize_track(
        crossing(entry=2.0, closest=2.0, exit_=2.0),
        policy(),
        longitude_evaluator(),
    )
    geometry = SatelliteExactTrackLayer(value).realize(
        LayerRealizationContext(value.coordinate_spec),
        observer=None,
    )

    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 1
    assert geometry.metadata["geometry_status"] == (
        "zero-duration visit; no segment"
    )


def test_exact_semantics_are_stable_distinct_and_noncolliding():
    one = track()
    other = _realize_track(
        crossing(field_id="field-two"),
        policy(),
        longitude_evaluator(),
    )
    path = semantic_layer_identity(SatelliteExactTrackLayer(one))
    events = semantic_layer_identity(SatelliteExactTrackEventsLayer(one))
    other_path = semantic_layer_identity(SatelliteExactTrackLayer(other))

    assert path.semantic_path[:3] == (
        "sky",
        "artificial_satellites",
        "exact_local_tracks",
    )
    assert path.semantic_path[-1] == "track"
    assert events.semantic_path[-1] == "events"
    assert path.semantic_path != other_path.semantic_path
    assert "satchecker_candidates" not in path.semantic_path


def test_coordinate_service_handles_fixed_gcrs_axis_orientation():
    value = track()
    target = CoordinateSpec(
        frame="icrs",
        origin="topocentric-direction",
        position_status=PositionStatus.GEOMETRIC,
        provider="test chart",
    )
    geometry = SatelliteExactTrackLayer(value).realize(
        LayerRealizationContext(target),
        observer=None,
    )

    assert geometry.coordinate_spec == target
    np.testing.assert_allclose(
        geometry.lon_deg[0],
        [item.longitude_deg for item in value.samples],
        atol=1e-12,
    )
    np.testing.assert_allclose(
        geometry.lat_deg[0],
        [item.latitude_deg for item in value.samples],
        atol=1e-12,
    )


def test_realizer_composes_snapshot_bound_factories_once_and_uses_no_provider():
    snapshot = load_snapshot()
    record = snapshot.records[0]
    digest = snapshot.manifest.content_sha256
    identity = SatelliteIdentity(
        record.norad_catalog_id,
        record.object_name,
        record.international_designator,
        record.classification,
    )
    value = crossing(
        identifier=record.norad_catalog_id,
        snapshot_sha256=digest,
        orbit_solution_id=record.source_identity,
        element_epoch=record.epoch_utc,
        identity=identity,
    )
    construction = {"propagator": 0, "transformer": 0}

    class FakePropagator:
        def __init__(self, supplied_record, *, snapshot_sha256):
            assert supplied_record is record
            assert snapshot_sha256 == digest
            construction["propagator"] += 1

        def propagate(self, instant_utc):
            return SimpleNamespace(
                evaluation_utc=instant_utc,
                sgp4_version="test",
                implementation="fake accepted seam",
                gravity_model="WGS-72",
            )

    class FakeTransformer:
        def __init__(self):
            construction["transformer"] += 1

        def transform(self, state, supplied_observer):
            seconds = (
                datetime.fromisoformat(
                    state.evaluation_utc.replace("Z", "+00:00")
                )
                - START
            ).total_seconds()
            return SimpleNamespace(
                gcrs_axis_longitude_deg=seconds,
                gcrs_axis_latitude_deg=0.0,
                range_km=500.0,
                teme_state=state,
                earth_orientation=SimpleNamespace(source_sha256="b" * 64),
                provenance=("fake topocentric composition",),
                warnings=(),
            )

    realized = ExactLocalSatelliteTrackRealizer(
        propagator_factory=FakePropagator,
        transformer_factory=FakeTransformer,
    ).realize(value, snapshot, policy())

    assert construction == {"propagator": 1, "transformer": 1}
    assert realized.crossing is value
    assert realized.samples[0].instant_utc == value.entry_instant
    assert realized.samples[-1].instant_utc == value.exit_instant
    assert all("snapshot SHA-256" in item.provenance[0] for item in realized.samples)


def test_realizer_rejects_snapshot_identity_mismatch_before_evaluation():
    snapshot = load_snapshot()
    with pytest.raises(ValueError, match="snapshot digest"):
        ExactLocalSatelliteTrackRealizer().realize(
            crossing(snapshot_sha256="f" * 64),
            snapshot,
            policy(),
        )

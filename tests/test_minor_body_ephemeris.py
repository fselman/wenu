"""Offline minor-body resource-chain and state-provider contracts."""

from hashlib import sha256
from types import SimpleNamespace

import numpy as np
import pytest
from skyfield.constants import AU_KM

from wenu.ephemeris import (
    EphemerisResourceChain,
    EphemerisResourceIdentity,
    EphemerisState,
    EphemerisStateRequest,
    EphemerisStateSource,
)
from wenu.minor_body_ephemeris import (
    EphemerisCompositionError,
    MinorBodyEphemerisState,
    MinorBodySolutionIdentity,
    SkyfieldMinorBodyStateSource,
    SpiceMinorBodyKernel,
    SpiceMinorBodySegment,
    UnsupportedEphemerisTimeScaleError,
)
from wenu.skyfield_ephemeris import (
    EphemerisCoverageError,
    EphemerisTargetError,
    UnsupportedEphemerisFrameError,
)


class FakeSegment:
    def __init__(self, target, centre, start, end, position, velocity):
        self.target = target
        self.center = centre
        self.spk_segment = SimpleNamespace(start_jd=start, end_jd=end)
        self._position = position
        self._velocity = velocity

    def at(self, time):
        return SimpleNamespace(
            position=SimpleNamespace(au=self._position),
            velocity=SimpleNamespace(au_per_d=self._velocity),
        )


class FakeKernel:
    def __init__(self, path, segments):
        self.path = str(path)
        self.segments = tuple(segments)


class FakeTimescale:
    def __init__(self, tdb):
        self.tdb = tdb
        self.received = []

    def from_astropy(self, value):
        self.received.append(value)
        return SimpleNamespace(tdb=self.tdb)


class PlanetarySource:
    def __init__(self, resource):
        self.resource = resource
        self.requests = []

    def state(self, request):
        self.requests.append(request)
        return EphemerisState(
            request=request,
            position=(0.5, 1.0, 1.5),
            velocity=(0.05, 0.1, 0.15),
            position_unit="au",
            velocity_unit="au/day",
            resource=self.resource,
            provider_target_id=request.target,
            provider_centre_id="0",
            provenance=("deterministic planetary state",),
        )


def resource():
    return EphemerisResourceIdentity(
        provider="Skyfield/JPL SPK",
        model="DE440",
        filename="de440s.bsp",
        sha256="a" * 64,
        coverage_start="JD 2400000.50000000",
        coverage_end="JD 2500000.50000000",
        coverage_time_scale="tdb",
    )


def solution(**overrides):
    values = dict(
        provider="JPL Horizons",
        service_version="Horizons API 1.3",
        wenu_target="ceres",
        object_class="asteroid",
        primary_designation="1 Ceres",
        horizons_command="1;",
        provider_spk_id="2000001",
        orbit_solution_id="JPL 49",
        solution_date="2026-09-10",
        osculating_epoch="2461200.5 TDB",
        reference_system="J2000 ecliptic and equinox",
        iau_number=1,
        name="Ceres",
        aliases=("A899 OF",),
        model_parameters=(("dynamical model", "JPL 49"),),
        quality_fields=(("condition code", "0"),),
        provenance=("SBDB solution snapshot",),
    )
    values.update(overrides)
    return MinorBodySolutionIdentity(**values)


def request(**overrides):
    values = dict(
        target="ceres",
        centre="solar system barycenter",
        frame="icrf",
        instant="2026-09-10T00:00:00",
        time_scale="tdb",
    )
    values.update(overrides)
    return EphemerisStateRequest(**values)


@pytest.fixture
def resolved(tmp_path):
    path = tmp_path / "ceres-horizons.bsp"
    path.write_bytes(b"deterministic synthetic Horizons SPK")
    segments = (
        FakeSegment(
            2000001,
            10,
            2460000.5,
            2470000.5,
            (2.0, 3.0, 4.0),
            (0.2, 0.3, 0.4),
        ),
    )
    kernel = FakeKernel(path, segments)
    planetary = PlanetarySource(resource())
    timescale = FakeTimescale(2461282.5)
    source = SkyfieldMinorBodyStateSource.from_kernels(
        small_body_kernel=kernel,
        planetary_source=planetary,
        timescale=timescale,
        solution=solution(),
        model="Horizons Ceres JPL 49",
    )
    return source, planetary, timescale, path


def test_solution_identity_keeps_identity_roles_separate():
    identity = solution(
        object_class=" ASTEROID ",
        provider_spk_id="02000001",
        aliases=["A899 OF"],
    )

    assert identity.wenu_target == "ceres"
    assert identity.provider == "JPL Horizons"
    assert identity.primary_designation == "1 Ceres"
    assert identity.horizons_command == "1;"
    assert identity.provider_spk_id == "2000001"
    assert identity.object_class == "asteroid"
    assert identity.aliases == ("A899 OF",)
    assert identity.model_parameters == (("dynamical model", "JPL 49"),)
    assert identity.quality_fields == (("condition code", "0"),)


@pytest.mark.parametrize("object_class", ("planet", "", "active asteroid"))
def test_solution_identity_rejects_unsupported_object_class(object_class):
    with pytest.raises(ValueError, match="object_class"):
        solution(object_class=object_class)


def test_provider_retains_resource_chain_and_ordered_segments(resolved):
    source, planetary, _, path = resolved

    assert isinstance(source, EphemerisStateSource)
    assert isinstance(source.resource, EphemerisResourceChain)
    assert source.resource.primary.filename == path.name
    assert (
        source.resource.primary.sha256 == sha256(path.read_bytes()).hexdigest()
    )
    assert source.resource.dependencies == (planetary.resource,)
    assert (
        "ordered segment 0: target 2000001, centre 10"
        in (source.resource.provenance[2])
    )
    assert not hasattr(source, "close")


def test_provider_composes_segment_centre_through_planetary_source(resolved):
    source, planetary, timescale, _ = resolved

    state = source.state(request())

    assert isinstance(state, MinorBodyEphemerisState)
    assert isinstance(state, EphemerisState)
    assert state.position == (2.5, 4.0, 5.5)
    assert state.velocity == pytest.approx((0.25, 0.4, 0.55))
    assert state.position_unit == "au"
    assert state.velocity_unit == "au/day"
    assert state.resource is source.resource
    assert state.provider_target_id == "2000001"
    assert state.provider_centre_id == "0"
    assert state.solution is source.solution
    assert state.segment.index == 0
    assert state.segment.frame_id == 1
    assert state.segment.data_type is None
    assert state.request == request()
    assert planetary.requests == [
        EphemerisStateRequest(
            target="10",
            centre="solar system barycenter",
            frame="icrf",
            instant="2026-09-10T00:00:00",
            time_scale="tdb",
        )
    ]
    assert timescale.received[0].scale == "tdb"
    assert "orbit solution: JPL 49" in state.provenance


def test_provider_uses_later_overlapping_segment_as_spk_priority(tmp_path):
    path = tmp_path / "priority.bsp"
    path.write_bytes(b"priority")
    segments = (
        FakeSegment(2000001, 10, 2460000.5, 2470000.5, (1, 1, 1), (1, 1, 1)),
        FakeSegment(2000001, 10, 2461000.5, 2462000.5, (2, 2, 2), (2, 2, 2)),
    )
    planetary = PlanetarySource(resource())
    source = SkyfieldMinorBodyStateSource.from_kernels(
        small_body_kernel=FakeKernel(path, segments),
        planetary_source=planetary,
        timescale=FakeTimescale(2461282.5),
        solution=solution(),
        model="Horizons priority test",
    )

    state = source.state(request())

    assert state.position == (2.5, 3.0, 3.5)
    assert "selected ordered segment: 1" in state.provenance


def test_provider_retains_disjoint_segments_and_rejects_the_gap(tmp_path):
    path = tmp_path / "disjoint.bsp"
    path.write_bytes(b"disjoint")
    segments = (
        FakeSegment(2000001, 10, 2460000.5, 2461000.5, (1, 1, 1), (1, 1, 1)),
        FakeSegment(2000001, 10, 2462000.5, 2463000.5, (2, 2, 2), (2, 2, 2)),
    )
    planetary = PlanetarySource(resource())
    timescale = FakeTimescale(2461500.5)
    source = SkyfieldMinorBodyStateSource.from_kernels(
        small_body_kernel=FakeKernel(path, segments),
        planetary_source=planetary,
        timescale=timescale,
        solution=solution(),
        model="Horizons disjoint test",
    )

    assert source.resource.primary.coverage_start == "JD 2460000.50000000"
    assert source.resource.primary.coverage_end == "JD 2463000.50000000"
    with pytest.raises(EphemerisCoverageError, match="segment coverage"):
        source.state(request())


@pytest.mark.parametrize(
    ("overrides", "error", "message"),
    (
        ({"target": "halley"}, EphemerisTargetError, "does not match"),
        ({"frame": "gcrs"}, UnsupportedEphemerisFrameError, "frame='icrf'"),
        (
            {"time_scale": "utc"},
            UnsupportedEphemerisTimeScaleError,
            "time_scale='tdb'",
        ),
    ),
)
def test_provider_rejects_wrong_identity_frame_or_time(
    resolved,
    overrides,
    error,
    message,
):
    source, _, _, _ = resolved

    with pytest.raises(error, match=message):
        source.state(request(**overrides))


def test_provider_fails_closed_outside_small_body_coverage(resolved):
    source, _, timescale, _ = resolved
    timescale.tdb = 2500001.5

    with pytest.raises(EphemerisCoverageError, match="segment coverage"):
        source.state(request())


def test_provider_rejects_incompatible_planetary_state(resolved):
    source, planetary, _, _ = resolved
    original_state = planetary.state

    def wrong_units(request):
        state = original_state(request)
        return EphemerisState(
            request=state.request,
            position=state.position,
            velocity=state.velocity,
            position_unit="km",
            velocity_unit="km/day",
            resource=state.resource,
        )

    planetary.state = wrong_units

    with pytest.raises(EphemerisCompositionError, match="AU and AU/day"):
        source.state(request())


def test_spice_kernel_evaluates_exact_type_21_segment(monkeypatch, tmp_path):
    path = tmp_path / "horizons-type-21.bsp"
    path.write_bytes(b"synthetic DAF bytes")
    start_et = 100.0
    end_et = 200.0
    integers = np.array((2000001, 10, 1, 21, 1000, 2000))
    descriptor = np.arange(5, dtype=float)
    calls = []
    found = iter((True, False))

    monkeypatch.setattr("spiceypy.dafopr", lambda value: 7)
    monkeypatch.setattr(
        "spiceypy.dafbfs", lambda handle: calls.append(("search", handle))
    )
    monkeypatch.setattr("spiceypy.daffna", lambda: next(found))
    monkeypatch.setattr("spiceypy.dafgs", lambda size: descriptor)
    monkeypatch.setattr(
        "spiceypy.dafus",
        lambda summary, nd, ni: (np.array((start_et, end_et)), integers),
    )
    monkeypatch.setattr(
        "spiceypy.spkpvn",
        lambda handle, summary, et: (
            1,
            np.array((AU_KM, 2 * AU_KM, 3 * AU_KM, AU_KM / 86400, 0, 0)),
            10,
        ),
    )
    monkeypatch.setattr(
        "spiceypy.dafcls", lambda handle: calls.append(("close", handle))
    )

    with SpiceMinorBodyKernel(path) as kernel:
        assert len(kernel.segments) == 1
        segment = kernel.segments[0]
        assert isinstance(segment, SpiceMinorBodySegment)
        assert segment.target == 2000001
        assert segment.center == 10
        assert segment.data_type == 21
        result = segment.at(SimpleNamespace(tdb=2451545.0))

    assert result.position.au == pytest.approx((1.0, 2.0, 3.0))
    assert result.velocity.au_per_d == pytest.approx((1.0, 0.0, 0.0))
    assert calls == [("search", 7), ("close", 7)]


def test_spice_kernel_rejects_use_after_close(monkeypatch, tmp_path):
    path = tmp_path / "closed.bsp"
    path.write_bytes(b"synthetic DAF bytes")
    monkeypatch.setattr("spiceypy.dafopr", lambda value: 7)
    monkeypatch.setattr("spiceypy.dafbfs", lambda handle: None)
    found = iter((True, False))
    monkeypatch.setattr("spiceypy.daffna", lambda: next(found))
    monkeypatch.setattr("spiceypy.dafgs", lambda size: np.zeros(5))
    monkeypatch.setattr(
        "spiceypy.dafus",
        lambda summary, nd, ni: (
            np.array((0.0, 86400.0)),
            np.array((2000001, 10, 1, 21, 1, 2)),
        ),
    )
    monkeypatch.setattr("spiceypy.dafcls", lambda handle: None)
    kernel = SpiceMinorBodyKernel(path)
    segment = kernel.segments[0]
    kernel.close()

    with pytest.raises(ValueError, match="closed"):
        segment.at(SimpleNamespace(tdb=2451545.0))


def test_provider_rejects_kernel_without_declared_target(tmp_path):
    path = tmp_path / "wrong-target.bsp"
    path.write_bytes(b"wrong target")
    planetary = PlanetarySource(resource())

    with pytest.raises(EphemerisTargetError, match="2000001"):
        SkyfieldMinorBodyStateSource.from_kernels(
            small_body_kernel=FakeKernel(
                path,
                (
                    FakeSegment(
                        2000002,
                        10,
                        2460000.5,
                        2470000.5,
                        (1, 2, 3),
                        (1, 2, 3),
                    ),
                ),
            ),
            planetary_source=planetary,
            timescale=FakeTimescale(2461282.5),
            solution=solution(),
            model="wrong target",
        )

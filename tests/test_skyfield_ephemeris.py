from hashlib import sha256
from types import SimpleNamespace

import pytest

from wenu.ephemeris import EphemerisStateRequest, EphemerisStateSource
from wenu.skyfield_ephemeris import (
    EphemerisCoverageError,
    EphemerisTargetError,
    SkyfieldEphemerisStateSource,
    UnsupportedEphemerisFrameError,
    resolve_skyfield_resource_identity,
    skyfield_observer_barycentric_state,
)


class FakeSegment:
    def __init__(self, start, end):
        self.spk_segment = SimpleNamespace(start_jd=start, end_jd=end)


class FakeTime:
    def __init__(self, tdb):
        self.tdb = tdb


class FakeTimescale:
    def __init__(self, tdb):
        self.tdb = tdb
        self.received = []

    def from_astropy(self, value):
        self.received.append(value)
        return FakeTime(self.tdb)


class FakeVector:
    def __init__(self, position, velocity):
        self.position = position
        self.velocity = velocity

    def __sub__(self, other):
        return FakeVector(
            tuple(a - b for a, b in zip(self.position, other.position)),
            tuple(a - b for a, b in zip(self.velocity, other.velocity)),
        )

    def at(self, time):
        return SimpleNamespace(
            position=SimpleNamespace(au=self.position),
            velocity=SimpleNamespace(au_per_d=self.velocity),
        )


class FakeKernel:
    def __init__(self, path):
        self.path = str(path)
        self.segments = (
            FakeSegment(2400000.5, 2500000.5),
            FakeSegment(2410000.5, 2490000.5),
        )
        self._ids = {
            "solar system barycenter": 0,
            "venus": 299,
            "earth": 399,
        }
        self._vectors = {
            0: FakeVector((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            299: FakeVector((1.0, 2.0, 3.0), (0.1, 0.2, 0.3)),
            399: FakeVector((0.4, 0.5, 0.6), (0.01, 0.02, 0.03)),
        }

    def decode(self, key):
        try:
            return self._ids[key]
        except KeyError as error:
            raise ValueError(key) from error

    def __getitem__(self, key):
        return self._vectors[key]


def request(**overrides):
    values = dict(
        target="venus",
        centre="solar system barycenter",
        frame="icrf",
        instant="2026-08-30T00:00:00",
        time_scale="tdb",
    )
    values.update(overrides)
    return EphemerisStateRequest(**values)


@pytest.fixture
def resolved(tmp_path):
    path = tmp_path / "de440s.bsp"
    path.write_bytes(b"wenu deterministic fake SPK")
    kernel = FakeKernel(path)
    timescale = FakeTimescale(2461282.5)
    observer = SimpleNamespace(ephemeris=kernel, timescale=timescale)
    source = SkyfieldEphemerisStateSource.from_observer(observer)
    return source, kernel, timescale, path


def test_resolved_resource_hashes_exact_borrowed_file_once(resolved):
    source, kernel, _, path = resolved
    identity = source.resource

    assert identity.provider == "Skyfield/JPL SPK"
    assert identity.model == "DE440"
    assert identity.filename == "de440s.bsp"
    assert identity.sha256 == sha256(path.read_bytes()).hexdigest()
    assert identity.coverage_start == "JD 2410000.50000000"
    assert identity.coverage_end == "JD 2490000.50000000"
    assert identity.coverage_time_scale == "tdb"
    assert source._kernel is kernel


def test_adapter_returns_complete_geometric_icrf_state(resolved):
    source, _, timescale, _ = resolved

    state = source.state(request())

    assert isinstance(source, EphemerisStateSource)
    assert state.position == (1.0, 2.0, 3.0)
    assert state.velocity == (0.1, 0.2, 0.3)
    assert state.position_unit == "au"
    assert state.velocity_unit == "au/day"
    assert state.provider_target_id == "299"
    assert state.provider_centre_id == "0"
    assert state.resource is source.resource
    assert "simultaneous geometric" in state.provenance[0]
    assert timescale.received[0].scale == "tdb"


def test_adapter_subtracts_independent_barycentric_states(resolved):
    source, _, _, _ = resolved

    state = source.state(request(centre="earth"))

    assert state.position == pytest.approx((0.6, 1.5, 2.4))
    assert state.velocity == pytest.approx((0.09, 0.18, 0.27))
    assert state.provider_centre_id == "399"


def test_adapter_rejects_unsupported_cartesian_frame(resolved):
    source, _, _, _ = resolved

    with pytest.raises(
        UnsupportedEphemerisFrameError,
        match="only frame='icrf'",
    ):
        source.state(request(frame="gcrs"))


def test_adapter_reports_unknown_target_deterministically(resolved):
    source, _, _, _ = resolved

    with pytest.raises(EphemerisTargetError, match="target 'mars'"):
        source.state(request(target="mars"))


def test_adapter_rejects_instant_outside_aggregate_coverage(resolved):
    source, _, timescale, _ = resolved
    timescale.tdb = 2600000.5

    with pytest.raises(EphemerisCoverageError, match="outside kernel coverage"):
        source.state(request())


def test_non_de_filename_requires_explicit_model(tmp_path):
    path = tmp_path / "custom.bsp"
    path.write_bytes(b"custom")
    kernel = FakeKernel(path)

    with pytest.raises(ValueError, match="model must be supplied"):
        resolve_skyfield_resource_identity(kernel)

    identity = resolve_skyfield_resource_identity(
        kernel,
        model="research solution",
    )
    assert identity.model == "research solution"


def test_adapter_does_not_claim_or_close_borrowed_resource(resolved):
    source, kernel, _, _ = resolved

    assert source._kernel is kernel
    assert not hasattr(source, "close")


def test_observer_state_adapter_preserves_site_and_reception_state(resolved):
    source, _, _, _ = resolved
    skyfield_state = SimpleNamespace(
        position=SimpleNamespace(au=(1.0, 2.0, 3.0)),
        velocity=SimpleNamespace(au_per_d=(0.1, 0.2, 0.3)),
    )
    observer = SimpleNamespace(
        ephemeris=source._kernel,
        skyfield=SimpleNamespace(at=lambda time: skyfield_state),
        t=object(),
        t_astropy=SimpleNamespace(
            isot="2026-08-30T00:00:00.000",
            scale="utc",
        ),
        location_name="La Ligua",
    )

    state = skyfield_observer_barycentric_state(
        observer,
        source=source,
    )

    assert state.observer_id == "La Ligua"
    assert state.centre == "solar system barycenter"
    assert state.frame == "icrf"
    assert state.instant == "2026-08-30T00:00:00.000"
    assert state.time_scale == "utc"
    assert state.position == (1.0, 2.0, 3.0)
    assert state.velocity == (0.1, 0.2, 0.3)
    assert state.resource is source.resource
    assert "Earth plus WGS84 site" in state.provenance[0]


def test_observer_state_adapter_requires_the_same_borrowed_kernel(resolved):
    source, _, _, _ = resolved
    observer = SimpleNamespace(ephemeris=object())

    with pytest.raises(ValueError, match="same ephemeris"):
        skyfield_observer_barycentric_state(observer, source=source)

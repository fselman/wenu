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
            "sun": 10,
            "venus": 299,
            "earth": 399,
        }
        self._vectors = {
            0: FakeVector((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            10: FakeVector((0.2, 0.3, 0.4), (0.01, 0.02, 0.03)),
            299: FakeVector((1.0, 2.0, 3.0), (0.1, 0.2, 0.3)),
            399: FakeVector((0.4, 0.5, 0.6), (0.01, 0.02, 0.03)),
        }

    def decode(self, key):
        if isinstance(key, int) and key in self._vectors:
            return key
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
    assert identity.model == "unqualified SPK model"
    assert "filename is not model evidence" in identity.provenance[-1]
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


def test_adapter_accepts_an_explicit_numeric_provider_target(resolved):
    source, _, _, _ = resolved

    state = source.state(request(target="10"))

    assert state.position == (0.2, 0.3, 0.4)
    assert state.provider_target_id == "10"


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


def test_filename_does_not_qualify_model_and_explicit_declaration_is_labelled(tmp_path):
    path = tmp_path / "custom.bsp"
    path.write_bytes(b"custom")
    kernel = FakeKernel(path)

    unknown = resolve_skyfield_resource_identity(kernel)
    assert unknown.model == "unqualified SPK model"
    renamed = tmp_path / "de999.bsp"
    path.rename(renamed)
    kernel.path = str(renamed)
    same_bytes = resolve_skyfield_resource_identity(kernel)
    assert same_bytes.sha256 == unknown.sha256
    assert same_bytes.model == unknown.model

    identity = resolve_skyfield_resource_identity(
        kernel,
        model="research solution",
    )
    assert identity.model == "research solution"
    assert "not independently qualified" in identity.provenance[-1]


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


@pytest.mark.parametrize('centre', ['solar system barycenter', 'earth'])
def test_cartesian_kernel_transport_preserves_existing_raw_geometric_state(resolved, centre):
    from wenu.ephemeris_state import KernelEphemerisStateSource
    source, kernel, _, _ = resolved
    query = request(centre=centre)
    raw = source.state(query)
    routed = KernelEphemerisStateSource(source).state(query)
    assert routed.position == pytest.approx(raw.position, rel=5e-16, abs=1e-16)
    assert routed.velocity == pytest.approx(raw.velocity, rel=5e-16, abs=1e-16)
    assert routed.request is query
    assert routed.provider_target_id == raw.provider_target_id == '299'
    assert routed.provider_centre_id == raw.provider_centre_id
    assert routed.resource is raw.resource
    assert routed.provenance[:-1] == raw.provenance
    assert source._kernel is kernel


def _synthetic_pinned_resources(tmp_path, monkeypatch):
    """Synthetic SPK bytes/metadata and vectors, not captured provider fixtures."""
    from skyfield import api
    from wenu.skyfield_ephemeris import PinnedEphemerisResource
    class PrecisionTimescale:
        def __init__(self): self.received = []
        def from_astropy(self, time):
            raise AssertionError('Exact TDB must not use an ISO/TT time route')
        def tdb_jd(self, jd, fraction=None):
            assert fraction is not None
            self.received.append((jd, fraction))
            return SimpleNamespace(jd1=jd, jd2=fraction)
    class PrecisionVector(FakeVector):
        def at(self, time):
            return SimpleNamespace(position=SimpleNamespace(au=tuple(x+time.jd2 for x in self.position)),
                velocity=SimpleNamespace(au_per_d=self.velocity))
    domains = [('DE440','full',(2451540.,2451550.)),
               ('DE441','part-1',(0.,2451546.)),
               ('DE441','part-2',(2451544.,8000000.))]
    kernels, pins = {}, []
    for index,(model,part,coverage) in enumerate(domains):
        path = tmp_path/f'synthetic-{index}.bsp'
        path.write_bytes(('synthetic SPK '+str(index)).encode())
        kernel = FakeKernel(path)
        kernel.segments = tuple(SimpleNamespace(spk_segment=SimpleNamespace(
            center=c, target=t, frame=1, data_type=2, start_jd=coverage[0],end_jd=coverage[1]))
            for c,t in ((0,3),(3,399),(0,10)))
        kernel._vectors[3] = FakeVector((9.,9.,9.),(.9,.9,.9))
        for key in (10,399):
            old = kernel._vectors[key]
            kernel._vectors[key] = PrecisionVector(old.position,old.velocity)
        kernel.closed = 0
        def close(k=kernel): k.closed += 1
        kernel.close = close
        kernels[str(path)] = kernel
        pins.append(PinnedEphemerisResource(str(path),sha256(path.read_bytes()).hexdigest(),
            model,part,coverage,('synthetic metadata; no JPL accuracy claim',)))
    timescale = PrecisionTimescale()
    monkeypatch.setattr(api,'load_file',lambda path:kernels[path])
    monkeypatch.setattr(api.load,'timescale',lambda *,builtin:timescale if builtin is True else None)
    return pins,kernels,timescale


def test_offline_companion_selection_exact_edges_and_resource_lifetime(tmp_path, monkeypatch):
    from wenu.skyfield_ephemeris import open_pinned_ephemerides
    from wenu.ephemeris import EphemerisJulianDate
    pins,kernels,_ = _synthetic_pinned_resources(tmp_path,monkeypatch)
    with open_pinned_ephemerides(reversed(pins)) as resources:
        for day,frac,role in ((2451540,0,'full'),(2451550,0,'full'),
            (2451540,-2**-40,'part-1'),(2451550,2**-40,'part-2'),
            (990545,0,'part-1'),(3000000,0,'part-2'),
            (0,0,'part-1'),(8000000,0,'part-2')):
            assert resources.select(EphemerisJulianDate(day,frac))[1]['part'] == role
        # Qualify deterministic part-1 priority separately where DE440 masks the seam.
        from wenu.skyfield_ephemeris import OfflineEphemerisResources
        de441 = OfflineEphemerisResources(resources._entries[1:])
        assert de441.select(EphemerisJulianDate(2451545,0))[1]['part'] == 'part-1'
        assert de441.select(EphemerisJulianDate(2451546,2**-40))[1]['part'] == 'part-2'
        for event in (EphemerisJulianDate(0,-2**-40),EphemerisJulianDate(8000000,2**-40)):
            with pytest.raises(EphemerisCoverageError): resources.select(event)
    assert all(k.closed == 1 for k in kernels.values())
    with pytest.raises(ValueError): resources.select(EphemerisJulianDate(2451545,0))


def test_offline_companion_hash_path_and_partial_open_failures_close(tmp_path, monkeypatch):
    from dataclasses import replace
    from wenu.skyfield_ephemeris import open_pinned_ephemerides
    pins,kernels,_ = _synthetic_pinned_resources(tmp_path,monkeypatch)
    bad = [pins[0],replace(pins[1],sha256='a'*64),pins[2]]
    with pytest.raises(ValueError):
        with open_pinned_ephemerides(bad): pass
    assert list(k.closed for k in kernels.values()) == [1,1,0]
    for k in kernels.values():k.closed=0
    list(kernels.values())[1].segments[1].spk_segment.target = 301
    with pytest.raises(ValueError):
        with open_pinned_ephemerides(pins): pass
    assert list(k.closed for k in kernels.values()) == [1,1,0]
    with pytest.raises(ValueError):
        with open_pinned_ephemerides(pins[:2]): pass


def test_exact_companion_sdk_roundtrip_precision_and_direct_source(tmp_path, monkeypatch):
    from wenu.skyfield_ephemeris import open_pinned_ephemerides
    from wenu.ephemeris import EphemerisJulianDate
    from wenu.ephemeris_companion import prepare_ephemeris_companion, load_ephemeris_companion
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu_kernel.records import TimePoint
    pins,_,timescale = _synthetic_pinned_resources(tmp_path,monkeypatch)
    with open_pinned_ephemerides(pins) as resources:
        for index,day in enumerate((2451545,990545,3000000)):
            event = TimePoint(day,2**-40,'tdb')
            path = tmp_path/f'product-{index}'
            digest = prepare_ephemeris_companion(resources,event,path)
            saved = load_ephemeris_companion(path,expected_manifest_sha256=digest)
            assert saved.instant == event
            source,_ = resources.select(EphemerisJulianDate(day,2**-40))
            for row in saved.at(event):
                req = EphemerisStateRequest(row['target'],'0','icrf',EphemerisJulianDate(day,2**-40),'tdb')
                direct = source.state(req)
                routed = KernelEphemerisStateSource(source).state(req)
                assert tuple(row['position_au']) == routed.position
                assert tuple(row['velocity_au_per_day']) == routed.velocity
                assert row['position_au'] == pytest.approx(direct.position,rel=5e-16,abs=1e-16)
                assert row['velocity_au_per_day'] == pytest.approx(direct.velocity,rel=5e-16,abs=1e-16)
                assert row['position_error_au'] == dict(measurement=None,physical_model=None,numerical=None)
            assert (day,2**-40) in timescale.received
            with pytest.raises(FileExistsError): prepare_ephemeris_companion(resources,event,path)
        source,_ = resources.select(EphemerisJulianDate(2451545,0))
        exact = source.state(EphemerisStateRequest('399','0','icrf',EphemerisJulianDate(2451545,2**-40),'tdb'))
        rounded = source.state(EphemerisStateRequest('399','0','icrf',EphemerisJulianDate(2451545,0),'tdb'))
        assert exact.position != rounded.position  # deliberate summed-JD fault changes baseline


def test_exact_companion_publication_failure_cleanup_and_racing_destination(tmp_path, monkeypatch):
    from wenu.skyfield_ephemeris import open_pinned_ephemerides
    from wenu import ephemeris_companion as codec
    from wenu_kernel.records import TimePoint
    pins,_,_ = _synthetic_pinned_resources(tmp_path,monkeypatch)
    event = TimePoint(2451545,0,'tdb')
    original = codec.os.link
    with open_pinned_ephemerides(pins) as resources:
        for fail_at in (1,2):
            calls = []
            path = tmp_path/f'failed-{fail_at}'
            def fail(source,destination):
                calls.append(str(destination))
                if len(calls) == fail_at:raise OSError('injected link failure')
                return original(source,destination)
            with monkeypatch.context() as m:
                m.setattr(codec.os,'link',fail)
                with pytest.raises(OSError):codec.prepare_ephemeris_companion(resources,event,path)
            assert not path.exists()
            assert not list(tmp_path.glob('.wenu-ephemeris-*'))
        path = tmp_path/'racing'
        original_mkdir = codec.Path.mkdir
        def race(self,*args,**kwargs):
            if self == path and not self.exists():
                original_mkdir(self)
                (self/'other-writer').write_text('preserve')
            return original_mkdir(self,*args,**kwargs)
        with monkeypatch.context() as m:
            m.setattr(codec.Path,'mkdir',race)
            with pytest.raises(FileExistsError):codec.prepare_ephemeris_companion(resources,event,path)
        assert (path/'other-writer').read_text() == 'preserve'
        assert not list(tmp_path.glob('.wenu-ephemeris-*'))


def test_exact_companion_selected_backend_refusal_does_not_fallback(tmp_path, monkeypatch):
    from dataclasses import replace
    from wenu.skyfield_ephemeris import open_pinned_ephemerides
    from wenu.ephemeris import EphemerisJulianDate
    from wenu.ephemeris_companion import prepare_ephemeris_companion
    from wenu_kernel.records import TimePoint
    pins,_,_ = _synthetic_pinned_resources(tmp_path,monkeypatch)
    with open_pinned_ephemerides(pins) as resources:
        source,_ = resources.select(EphemerisJulianDate(2451545,0))
        state = source.state
        calls = []
        def wrong(req):
            calls.append(req.target)
            return replace(state(req),provider_target_id='3')
        monkeypatch.setattr(source,'state',wrong)
        with pytest.raises(ValueError):
            prepare_ephemeris_companion(resources,TimePoint(2451545,0,'tdb'),tmp_path/'wrong')
        assert calls == ['399']
        assert not (tmp_path/'wrong').exists()


def test_exact_companion_fresh_process_load_without_spk_or_provider(tmp_path, monkeypatch):
    import subprocess
    import sys
    from wenu.skyfield_ephemeris import open_pinned_ephemerides
    from wenu.ephemeris_companion import prepare_ephemeris_companion
    from wenu_kernel.records import TimePoint
    pins,_,_ = _synthetic_pinned_resources(tmp_path,monkeypatch)
    path = tmp_path/'detached'
    with open_pinned_ephemerides(pins) as resources:
        digest = prepare_ephemeris_companion(resources,TimePoint(2451545,0,'tdb'),path)
    for pin in pins:
        from pathlib import Path
        Path(pin.path).unlink()
    code = '''
import socket, sys
def refuse(*args, **kwargs):
    raise AssertionError('provider/network/SPK access forbidden during reload')
socket.socket.connect = refuse
from skyfield import api
api.load_file = refuse
api.load.__class__.__call__ = refuse
from wenu.ephemeris_companion import load_ephemeris_companion
import wenu.skyfield_ephemeris as sf
import wenu.ephemeris_state as sdk
sf.SkyfieldEphemerisStateSource.__init__ = refuse
sf.open_pinned_ephemerides = refuse
sdk.KernelEphemerisStateSource.__init__ = refuse
saved = load_ephemeris_companion(sys.argv[1], expected_manifest_sha256=sys.argv[2])
assert [r['target'] for r in saved.at(saved.instant)] == ['399','10']
print('data-only reload passed')
'''
    result = subprocess.run([sys.executable,'-c',code,str(path),digest],
                            capture_output=True,text=True,check=False)
    assert result.returncode == 0, result.stdout+result.stderr
    assert 'data-only reload passed' in result.stdout


def test_split_tdb_source_delivers_exact_event_to_real_skyfield_time(resolved, monkeypatch):
    """Real time backend plus synthetic vectors; not a real SPK orbit oracle."""
    from fractions import Fraction
    from skyfield.api import load
    from wenu.ephemeris import EphemerisJulianDate
    source,kernel,_,_ = resolved
    monkeypatch.setattr(source,'_timescale',load.timescale(builtin=True))
    # Synthetic vector admission for this event-input seam only.
    monkeypatch.setattr(source,'_coverage_jd',(-3100015.5,8000016.5))
    received=[]
    vector=kernel._vectors[399]
    old=vector.at
    def capture(time):
        received.append(Fraction(float(time.whole))+Fraction(float(time.tdb_fraction)))
        return old(time)
    monkeypatch.setattr(vector,'at',capture)
    for day in (2451545,990545,-1200955):
        for low in (2**-40,-2**-40):
            event=EphemerisJulianDate(day,low)
            source.state(EphemerisStateRequest('399','0','icrf',event,'tdb'))
            assert received[-1] == Fraction(day)+Fraction(low)
            assert received[-1] != Fraction(float(day+low))


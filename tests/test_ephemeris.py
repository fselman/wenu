"""Contracts for typed ephemeris-state sources."""

from dataclasses import FrozenInstanceError

import pytest

from wenu.coordinates import PositionStatus, observer_altaz_spec
from wenu.ephemeris import (
    EphemerisResourceChain,
    EphemerisResourceIdentity,
    EphemerisState,
    EphemerisStateRequest,
    EphemerisStateSource,
    ephemeris_resource_contains,
)

DIGEST = "a" * 64


def _resource(**overrides):
    values = dict(
        provider="JPL",
        model="DE440",
        filename="de440s.bsp",
        sha256=DIGEST,
        coverage_start="1849-12-26T00:00:00",
        coverage_end="2150-01-22T00:00:00",
        coverage_time_scale="TDB",
        provenance=("test resource",),
    )
    values.update(overrides)
    return EphemerisResourceIdentity(**values)


def _request(**overrides):
    values = dict(
        target="venus",
        centre="solar-system-barycenter",
        frame="ICRS",
        instant="2026-08-30T00:00:00",
        time_scale="TDB",
    )
    values.update(overrides)
    return EphemerisStateRequest(**values)


def _state(**overrides):
    values = dict(
        request=_request(),
        position=(1.0, 2.0, 3.0),
        velocity=(0.1, 0.2, 0.3),
        position_unit="km",
        velocity_unit="km/day",
        resource=_resource(),
        provider_target_id="299",
        provider_centre_id="0",
        provenance=("deterministic test state",),
    )
    values.update(overrides)
    return EphemerisState(**values)


def test_resource_identity_normalizes_digest_scale_and_provenance():
    resource = _resource(
        provider=" JPL ",
        sha256="ABCDEF" * 10 + "ABCD",
        coverage_time_scale=" TDB ",
        provenance=[" source segment "],
    )

    assert resource.provider == "JPL"
    assert resource.sha256 == ("abcdef" * 10 + "abcd")
    assert resource.coverage_time_scale == "tdb"
    assert resource.provenance == ("source segment",)


@pytest.mark.parametrize(
    "digest",
    ("a" * 63, "a" * 65, "g" * 64, ""),
)
def test_resource_identity_rejects_invalid_sha256(digest):
    with pytest.raises(ValueError, match="64 hexadecimal"):
        _resource(sha256=digest)


def test_resource_identity_is_frozen():
    resource = _resource()

    with pytest.raises(FrozenInstanceError):
        resource.model = "DE441"


def test_resource_chain_preserves_primary_dependencies_and_provenance():
    primary = _resource(filename="small-body.bsp", sha256="b" * 64)
    dependency = _resource()

    chain = EphemerisResourceChain(
        primary=primary,
        dependencies=[dependency],
        provenance=[" explicit composition "],
    )

    assert chain.primary is primary
    assert chain.dependencies == (dependency,)
    assert chain.provenance == ("explicit composition",)
    assert chain.provider == primary.provider
    assert chain.model == primary.model
    assert chain.filename == primary.filename
    assert chain.sha256 == primary.sha256
    assert ephemeris_resource_contains(chain, primary)
    assert ephemeris_resource_contains(chain, dependency)
    assert not ephemeris_resource_contains(chain, _resource(sha256="c" * 64))
    assert _state(resource=chain).resource is chain


def test_resource_chain_rejects_missing_duplicate_or_untyped_dependencies():
    primary = _resource(filename="small-body.bsp", sha256="b" * 64)

    with pytest.raises(ValueError, match="at least one"):
        EphemerisResourceChain(primary=primary, dependencies=())
    with pytest.raises(ValueError, match="distinct"):
        EphemerisResourceChain(primary=primary, dependencies=(primary,))
    with pytest.raises(TypeError, match="only EphemerisResourceIdentity"):
        EphemerisResourceChain(primary=primary, dependencies=(object(),))


def test_state_request_keeps_target_centre_frame_and_dynamical_time():
    request = _request(
        target=" venus ",
        centre=" solar-system-barycenter ",
        frame=" ICRS ",
        time_scale=" TDB ",
    )

    assert request.target == "venus"
    assert request.centre == "solar-system-barycenter"
    assert request.frame == "icrs"
    assert request.time_scale == "tdb"


@pytest.mark.parametrize("name", ("target", "centre", "frame", "instant"))
def test_state_request_rejects_blank_identity(name):
    with pytest.raises(ValueError, match=name):
        _request(**{name: " "})


def test_state_is_a_complete_immutable_six_component_value():
    state = _state(position=[1, 2, 3], velocity=[4, 5, 6])

    assert state.position == (1.0, 2.0, 3.0)
    assert state.velocity == (4.0, 5.0, 6.0)
    assert state.request.target == "venus"
    assert state.resource.sha256 == DIGEST

    with pytest.raises(FrozenInstanceError):
        state.position = (0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("position", (1.0, 2.0), "exactly three"),
        ("velocity", (1.0, 2.0, 3.0, 4.0), "exactly three"),
        ("position", (1.0, float("nan"), 3.0), "finite"),
        ("velocity", (1.0, float("inf"), 3.0), "finite"),
    ),
)
def test_state_rejects_incomplete_or_nonfinite_vectors(
    field, value, message
):
    with pytest.raises(ValueError, match=message):
        _state(**{field: value})


def test_state_rejects_position_only_input():
    values = dict(
        request=_request(),
        position=(1.0, 2.0, 3.0),
        position_unit="km",
        velocity_unit="km/day",
        resource=_resource(),
    )

    with pytest.raises(TypeError, match="velocity"):
        EphemerisState(**values)


def test_state_requires_typed_request_and_resource():
    with pytest.raises(TypeError, match="EphemerisStateRequest"):
        _state(request=object())
    with pytest.raises(TypeError, match="EphemerisResourceIdentity"):
        _state(resource=object())


def test_deterministic_source_satisfies_structural_protocol():
    class Source:
        def state(self, request):
            return _state(request=request)

    source = Source()
    request = _request()

    assert isinstance(source, EphemerisStateSource)
    assert source.state(request).request is request


def test_topocentric_status_is_removed_and_altaz_uses_apparent_status():
    assert "TOPOCENTRIC" not in PositionStatus.__members__

    class Observer:
        t_astropy = type(
            "Time",
            (),
            {"isot": "2026-08-30T00:00:00", "scale": "utc"},
        )()

    spec = observer_altaz_spec(
        Observer(), position_status=PositionStatus.APPARENT
    )

    assert spec.origin == "observer"
    assert spec.position_status is PositionStatus.APPARENT


def test_observer_altaz_spec_requires_explicit_position_status():
    class Observer:
        t_astropy = type(
            "Time",
            (),
            {"isot": "2026-08-30T00:00:00", "scale": "utc"},
        )()

    with pytest.raises(TypeError, match="position_status"):
        observer_altaz_spec(Observer())


def test_kernel_ephemeris_consumes_returned_si_states_and_refuses_after_success(monkeypatch):
    from dataclasses import replace
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability, ResourceMismatch
    from astropy import units as u

    resource = _resource()
    calls = []

    class Source:
        def __init__(self):
            self.resource = resource
        def state(self, request):
            calls.append(request)
            return _state(request=request, resource=self.resource,
                          position_unit='au', velocity_unit='au/day')
        def close(self):
            pytest.fail('adapter must never close a borrowed backend')

    source = Source()
    wrapper = KernelEphemerisStateSource(source)
    request = _request(frame='icrf')
    original_evaluate = KernelSession.evaluate
    seen = []

    def changed(session, query):
        batch = original_evaluate(session, query)
        seen.append(query)
        row = batch.states[0]
        assert row.source_epoch is None
        assert row.position_evidence.physical_model.status == 'not_evaluated'
        return replace(batch, states=(replace(
            row, position_m=(4 * u.au.to(u.m), 0.0, 0.0),
            velocity_m_s=(0.0, 0.0, 0.0)),))

    monkeypatch.setattr(KernelSession, 'evaluate', changed)
    state = wrapper.state(request)
    assert state.position == (4.0, 0.0, 0.0)
    assert state.velocity == (0.0, 0.0, 0.0)
    assert state.provider_target_id == '299'
    assert state.resource is resource
    assert calls == [request]
    assert seen[0].reference.origin_id == request.centre
    assert seen[0].reference.frame_id == 'icrf'
    assert seen[0].times[0].scale == 'tdb'
    assert seen[0].require_velocity

    def refuse(session, query):
        raise UnsupportedCapability('deliberate kernel refusal')
    monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    with pytest.raises(UnsupportedCapability, match='deliberate kernel refusal'):
        wrapper.state(request)
    assert calls == [request]
    source.resource = replace(resource, sha256='b' * 64)
    with pytest.raises(ResourceMismatch, match='identity changed'):
        wrapper.state(request)


def test_kernel_ephemeris_checks_returned_request_resource_units_and_coverage():
    from dataclasses import replace
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu_kernel.errors import KernelError, OutsideCoverage

    resource = _resource()
    request = _request(frame='icrf')

    class Source:
        def __init__(self, change):
            self.resource = resource
            self.change = change
        def state(self, actual):
            return self.change(_state(request=actual, resource=resource,
                                     position_unit='au', velocity_unit='au/day'))

    for change in (
        lambda state: replace(state, request=replace(request, target='moon')),
        lambda state: replace(state, resource=replace(resource, sha256='b' * 64)),
        lambda state: replace(state, position_unit='km'),
    ):
        with pytest.raises(KernelError):
            KernelEphemerisStateSource(Source(change)).state(request)

    def forbidden(state):
        pytest.fail('outside coverage must refuse before backend evaluation')
    with pytest.raises(OutsideCoverage):
        KernelEphemerisStateSource(Source(forbidden)).state(
            replace(request, instant='2200-01-01T00:00:00'))

def _synthetic_companion_bytes():
    """Constructed codec-only data; never captured JPL ephemeris evidence."""
    from hashlib import sha256
    from wenu.ephemeris_companion import _encode, REFERENCE, POLICY, SCHEMA, UNKNOWN_ERRORS
    source_names = ('wenu.ephemeris', 'wenu.ephemeris_state', 'wenu.skyfield_ephemeris',
                    'wenu.ephemeris_companion', 'wenu_kernel.kernel', 'wenu_kernel.records')
    rows = [dict(target=target, centre='0', position_au=[.1, .2, .3],
        velocity_au_per_day=[.001, .002, .003], position_error_au=UNKNOWN_ERRORS.copy(),
        velocity_error_au_per_day=UNKNOWN_ERRORS.copy(),
        provenance=['synthetic fixture; no physical validity', 'returned kernel Cartesian state'])
        for target in ('399', '10')]
    raw = _encode(rows)
    manifest = dict(schema=SCHEMA, complete=True,
        event=dict(jd1=2451545, jd2=2**-40, scale='tdb'), reference=REFERENCE.copy(),
        selection=dict(model='DE440', part='full', path='/synthetic/fixture.bsp', sha256='a'*64,
            coverage_jd=[2400000.5, 2500000.5], provenance=['synthetic metadata'],
            segments=[dict(centre=c, target=t, frame=1, data_type=2,
                start_jd=2400000.5, end_jd=2500000.5) for c,t in ((0,3), (3,399), (0,10))],
            policy=POLICY, spatial_convention='JPL TDB-compatible geometric ICRF',
            axes_evidence='SPK frame 1; JPL DE440/DE441 metadata explicitly admitted'),
        implementation=dict(sources={n:'b'*64 for n in source_names},
            backends={n:'synthetic' for n in ('skyfield','jplephem','astropy','numpy')}),
        stellar_link=None, products={'states.json':dict(sha256=sha256(raw).hexdigest(), size_bytes=len(raw))})
    return manifest, raw


def test_companion_data_only_exact_event_and_detached_rows(tmp_path):
    from hashlib import sha256
    from wenu.ephemeris_companion import _encode, EphemerisCompanion, load_ephemeris_companion
    from wenu_kernel.records import TimePoint
    manifest, raw = _synthetic_companion_bytes()
    saved = EphemerisCompanion(_encode(manifest), raw)
    event = saved.instant
    assert event == TimePoint(2451545, 2**-40, 'tdb')
    assert [r['target'] for r in saved.at(event, ('10','399'))] == ['10','399']
    assert saved.at(event, ()) == ()
    row = saved.at(event)[0]
    row['position_au'][0] = 999
    assert saved.at(event)[0]['position_au'][0] == .1
    for bad in (TimePoint(2451545, 0, 'tdb'), TimePoint(2451545, 2**-40, 'tcb')):
        with pytest.raises(ValueError): saved.at(bad)
    for ids in (('3',), ('399','399'), ('unknown',)):
        with pytest.raises(ValueError): saved.at(event, ids)
    (tmp_path/'manifest.json').write_bytes(saved.manifest)
    (tmp_path/'states.json').write_bytes(raw)
    assert load_ephemeris_companion(tmp_path, expected_manifest_sha256=
        sha256(saved.manifest).hexdigest()) == saved
    with pytest.raises(ValueError):
        load_ephemeris_companion(tmp_path, expected_manifest_sha256='c'*64)
    (tmp_path/'states.json').unlink()
    with pytest.raises(ValueError): load_ephemeris_companion(tmp_path)


def test_companion_rejects_semantic_corruption_even_with_rehashed_payload():
    import copy
    from hashlib import sha256
    from wenu.ephemeris_companion import _encode, _decode, EphemerisCompanion
    manifest, raw = _synthetic_companion_bytes()
    EphemerisCompanion(_encode(manifest), raw)  # passing baseline
    faults = [lambda m,r:m.update(complete=False), lambda m,r:m.update(schema='wrong'),
        lambda m,r:m['event'].update(scale='tcb'), lambda m,r:m['event'].update(jd2=.5),
        lambda m,r:m['reference'].update(frame='gcrs'), lambda m,r:m['reference'].update(centre='3'),
        lambda m,r:m['reference'].update(position_unit='km'),
        lambda m,r:m['selection'].update(model='DE440s'),
        lambda m,r:m['selection'].update(part='part-1'),
        lambda m,r:m['selection'].update(coverage_jd=[2451545,2451545.0000001]),
        lambda m,r:m['selection']['segments'][1].update(target=301),
        lambda m,r:m['selection']['segments'][0].update(frame=17),
        lambda m,r:m['selection']['segments'][0].update(data_type=99),
        lambda m,r:m['selection'].update(spatial_convention='nominal-astrometric'),
        lambda m,r:m['implementation']['sources'].update({'wenu.ephemeris':'wrong'}),
        lambda m,r:r[0].update(target='3'), lambda m,r:r[1].update(centre='399'),
        lambda m,r:r.pop(), lambda m,r:r[0].update(velocity_au_per_day=None),
        lambda m,r:r[0].update(position_error_au=0), lambda m,r:r[0].update(provenance=['synthetic'])]
    for fault in faults:
        m,r = copy.deepcopy(manifest),_decode(raw)
        fault(m,r)
        altered = _encode(r)
        m['products']['states.json'] = dict(sha256=sha256(altered).hexdigest(), size_bytes=len(altered))
        with pytest.raises((ValueError, TypeError)):
            EphemerisCompanion(_encode(m), altered)
    with pytest.raises(ValueError): EphemerisCompanion(_encode(manifest), raw+b' ')
    with pytest.raises(ValueError): EphemerisCompanion(_encode(manifest), raw.replace(b'0.1', b'NaN'))
    with pytest.raises(ValueError): EphemerisCompanion(b'{"schema":1,"schema":2}', raw)


def test_companion_validates_explicit_tcb_link_receipt():
    from dataclasses import asdict
    import copy
    from wenu.astrometric_coordinates import TcbTdbAdapter
    from wenu.ephemeris_companion import _encode, _decode, EphemerisCompanion
    from wenu_kernel.records import TimePoint, TimeSpan
    from wenu_kernel.time import TimeService
    m,raw = _synthetic_companion_bytes()
    source = TimePoint(2451545, 2**-40, 'tcb')
    adapter = TcbTdbAdapter(TimeSpan(TimePoint(2400001,0,'tcb'), TimePoint(2499999,0,'tcb')))
    admission = adapter.describe()
    receipt = TimeService((adapter,), admissions=(admission,)).convert(source,'tdb')
    m['event'] = asdict(receipt.target)
    m['stellar_link'] = _decode(_encode(dict(stellar_manifest_sha256='c'*64,
        stellar_event=asdict(source), admission=asdict(admission), conversion=asdict(receipt))))
    saved = EphemerisCompanion(_encode(m),raw)
    assert saved.instant == receipt.target
    for key in ('source', 'target'):
        bad = copy.deepcopy(m)
        bad['stellar_link']['conversion'][key]['jd2'] += 2**-30
        with pytest.raises(ValueError): EphemerisCompanion(_encode(bad),raw)
    bad = copy.deepcopy(m)
    bad['stellar_link']['conversion']['numerical_error_s'] = 0
    # This exact conversion has nonzero operation rounding; it cannot be relabelled exact.
    assert receipt.numerical_error_s > 0
    with pytest.raises(ValueError): EphemerisCompanion(_encode(bad),raw)


def test_ephemeris_split_event_requires_native_tdb_and_canonical_parts():
    from wenu.ephemeris import EphemerisJulianDate, EphemerisStateRequest
    e = EphemerisJulianDate(-1200955,2**-40)
    assert EphemerisStateRequest('399','0','icrf',e,'tdb').instant == e
    with pytest.raises(ValueError): EphemerisStateRequest('399','0','icrf',e,'tcb')
    for args in ((True,0), (1,.5), (1,float('nan')), (2**53+1,0), (1,True)):
        with pytest.raises(ValueError): EphemerisJulianDate(*args)

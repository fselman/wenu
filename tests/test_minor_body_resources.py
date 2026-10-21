"""Manifest-backed minor-body source resolution and lifecycle contracts."""

import json
from pathlib import Path
from hashlib import sha256
from types import SimpleNamespace

import pytest

from wenu.comet_designations import parse_comet_designation
from wenu.minor_body_resources import (
    MinorBodyResourceCollection,
    MinorBodyResourceSession,
)
from wenu.sky.ceres import CERES_BODY
from tools import install_comet_resource


@pytest.mark.parametrize("fail_binding", [False, True])
def test_resolver_binding_is_atomic_and_deduplicates_layer_identity(fail_binding):
    from wenu.minor_body_resources import bind_sky_source_resolver, restore_sky_source_resolvers
    old, replacement = object(), object()

    class Point:
        def __init__(self, fail=False):
            self.value = old
            self.fail = fail
            self.writes = []

        @property
        def source_resolver(self):
            return self.value

        @source_resolver.setter
        def source_resolver(self, value):
            self.writes.append(value)
            if self.fail and value is replacement:
                raise RuntimeError("synthetic resolver setter failure")
            self.value = value

    first, second = Point(), Point(fail_binding)
    sky = SimpleNamespace(solar_system_bodies={"first": first, "alias": first, "second": second}, moon=first)
    if fail_binding:
        with pytest.raises(RuntimeError, match="synthetic resolver setter failure"):
            bind_sky_source_resolver(sky, replacement)
    else:
        previous = bind_sky_source_resolver(sky, replacement)
        assert len(previous) == 2
        assert first.source_resolver is second.source_resolver is replacement
        restore_sky_source_resolvers(previous)
    assert first.source_resolver is second.source_resolver is old
    assert first.writes == second.writes == [replacement, old]


def test_resolver_restore_attempts_other_bindings_after_one_setter_fails():
    from wenu.minor_body_resources import restore_sky_source_resolvers
    old, replacement = object(), object()
    class FailingPoint:
        @property
        def source_resolver(self):
            return replacement

        @source_resolver.setter
        def source_resolver(self, value):
            raise RuntimeError("synthetic restoration failure")
    first = FailingPoint()
    second = SimpleNamespace(source_resolver=replacement)
    with pytest.raises(RuntimeError, match="synthetic restoration failure"):
        restore_sky_source_resolvers(((first, old), (second, old)))
    assert second.source_resolver is old


def manifest_directory(tmp_path, *, digest=None, target="20000001"):
    payload = b"DAF/fake Ceres kernel"
    (tmp_path / "ceres.bsp").write_bytes(payload)
    record = {
        "key": "ceres",
        "filename": "ceres.bsp",
        "sha256": digest or sha256(payload).hexdigest(),
        "spk_file_id": target,
        "horizons_result": (
            "1 Ceres\nSoln.date: 2021-Apr-13_11:04:44\n"
            "soln ref.= JPL#48"
        ),
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": [record]}), encoding="utf-8"
    )
    return tmp_path


def install_fakes(monkeypatch, *, target=20000001, coverage=(0.0, 1.0)):
    closes = []
    kernels = []

    class Kernel:
        def __init__(self, path):
            self.path = path
            self.segments = (SimpleNamespace(
                target=target,
                center=10,
                frame_id=1,
                data_type=21,
                start_jd=coverage[0],
                end_jd=coverage[1],
            ),)
            kernels.append(self)

        def close(self):
            closes.append(self)

    planetary = SimpleNamespace(resource=SimpleNamespace(sha256="p" * 64))
    source = object()
    monkeypatch.setattr(
        "wenu.minor_body_resources.SpiceMinorBodyKernel", Kernel
    )
    monkeypatch.setattr(
        "wenu.minor_body_resources.SkyfieldEphemerisStateSource.from_observer",
        lambda observer: planetary,
    )
    monkeypatch.setattr(
        "wenu.minor_body_resources.SkyfieldMinorBodyStateSource.from_kernels",
        lambda **values: source,
    )
    return planetary, source, kernels, closes


def test_session_resolves_ceres_once_and_closes_one_kernel(tmp_path, monkeypatch):
    planetary, source, kernels, closes = install_fakes(monkeypatch)
    observer = SimpleNamespace(timescale=object())
    session = MinorBodyResourceSession(
        manifest_directory(tmp_path), observer
    )

    first = session.source_binding(CERES_BODY, observer)
    second = session.source_binding(CERES_BODY, observer)

    assert first.target_source is source
    assert first.observer_source is planetary
    assert second == first
    assert len(kernels) == 1
    session.close()
    session.close()
    assert closes == kernels


def test_session_rejects_digest_target_and_observer_mismatch(
    tmp_path, monkeypatch
):
    install_fakes(monkeypatch)
    observer = SimpleNamespace(timescale=object())
    directory = manifest_directory(tmp_path, digest="0" * 64)
    session = MinorBodyResourceSession(directory, observer)
    with pytest.raises(ValueError, match="digest differs"):
        session.source_binding(CERES_BODY, observer)
    with pytest.raises(ValueError, match="different observer"):
        session.source_binding(CERES_BODY, object())


def test_session_requires_manifest_and_declared_ceres_record(
    tmp_path, monkeypatch
):
    install_fakes(monkeypatch)
    observer = SimpleNamespace(timescale=object())
    with pytest.raises(FileNotFoundError, match="acquisition manifest"):
        MinorBodyResourceSession(tmp_path, observer)

    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": []}), encoding="utf-8"
    )
    session = MinorBodyResourceSession(tmp_path, observer)
    with pytest.raises(FileNotFoundError, match="no resource for 'ceres'"):
        session.source_binding(CERES_BODY, observer)


def numbered_manifest_directory(tmp_path, *, name=None):
    record = {
        "key": "79989",
        "filename": "79989.bsp",
        "sha256": "0" * 64,
        "spk_file_id": "20079989",
        "horizons_result": (
            "1999 FH4\nSoln.date: 2026-Sep-11\nsoln ref.= JPL#1"
        ),
        "identity": {
            "permanent_number": 79989,
            "primary_designation": "1999 FH4",
            "name": name,
            "object_class": "asteroid",
            "provider_spk_id": "20079989",
            "classifications": ["main_belt"],
        },
        "solution": {
            "provider": "NASA/JPL Horizons API",
            "service_version": "1.2",
            "object_class": "asteroid",
            "primary_designation": "1999 FH4",
            "horizons_command": "79989;",
            "provider_spk_id": "20079989",
            "orbit_solution_id": "JPL#1",
            "solution_date": "2026-Sep-11",
            "osculating_epoch": "2461294.5 TDB",
            "reference_system": "ICRF/J2000",
        },
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": [record]}), encoding="utf-8"
    )
    return tmp_path


def test_collection_resolves_number_and_installed_official_name(tmp_path):
    collection = MinorBodyResourceCollection(
        numbered_manifest_directory(tmp_path, name="Future Name")
    )

    numbered = collection.resolve("79989")
    named = collection.resolve("  future NAME ")

    assert named is numbered
    assert numbered.selection_key == "79989"
    assert numbered.entity_key == "asteroid_79989"
    assert numbered.canonical_designation == "Future Name (79989)"
    assert collection.solution_for(numbered).iau_number == 79989


def test_collection_rejects_uninstalled_name(tmp_path):
    collection = MinorBodyResourceCollection(
        numbered_manifest_directory(tmp_path)
    )

    with pytest.raises(KeyError, match="no installed object"):
        collection.resolve("not present")


def test_real_offline_ceres_kernel_route_matches_retained_science(tmp_path):
    """Use existing captured SPK evidence only; never acquire a test resource."""
    import shutil
    from dataclasses import replace
    import numpy as np
    from wenu.observer import Observer, DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS
    from wenu.ephemeris import EphemerisStateRequest
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu.sky.solar_system_points import EphemerisSourceBinding, SolarSystemPointLayer
    from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer
    from test_solar_system_tracks import CONTEXT, request
    data = Path(DEFAULT_DATA_DIRECTORY)
    directory = data/'minor_bodies'/'50a2'
    report = directory/'acquisition-report.json'
    for path in (report, data/DEFAULT_EPHEMERIS):
        if not path.is_file():
            raise FileNotFoundError(f'offline asteroid acceptance requires {path}')
    document = json.loads(report.read_text())
    record = next(r for r in document['resources'] if r['key']=='ceres')
    shutil.copyfile(directory/record['filename'],tmp_path/record['filename'])
    (tmp_path/'acquisition-report.json').write_text(json.dumps({'resources':[record]}))
    context = replace(CONTEXT,evaluation_instant='2026-08-30T00:00:00',evaluation_time_scale='utc')
    with Observer(location='La Ligua',time='2026-08-30T00:00:00Z') as observer:
        with MinorBodyResourceSession(tmp_path,observer) as session:
            binding=session.source_binding(CERES_BODY,observer)
            assert isinstance(binding.target_source,KernelEphemerisStateSource)
            raw=binding.target_source.source
            query=EphemerisStateRequest('ceres',CERES_BODY.centre,'icrf','2026-08-30T00:00:00','tdb')
            expected=raw.state(query);actual=binding.target_source.state(query)
            np.testing.assert_allclose(actual.position,expected.position,rtol=0,atol=1e-14)
            np.testing.assert_allclose(actual.velocity,expected.velocity,rtol=0,atol=1e-16)
            assert actual.solution is expected.solution and actual.segment is expected.segment
            resolver=lambda d,o:EphemerisSourceBinding(raw,binding.observer_source)
            before=SolarSystemPointLayer(CERES_BODY,source_resolver=resolver).realize(context,observer)
            after=SolarSystemPointLayer(CERES_BODY,source_resolver=session.source_binding).realize(context,observer)
            np.testing.assert_allclose(after.lon_deg,before.lon_deg,rtol=0,atol=1e-11)
            np.testing.assert_allclose(after.lat_deg,before.lat_deg,rtol=0,atol=1e-11)
            value=request(descriptor=CERES_BODY,sample_step_days=.5,tick_step_days=.75,tick_count=1)
            before=SolarSystemTrackRealizer(source_resolver=resolver).curve(value,context=context,observer=observer)
            after=SolarSystemTrackRealizer(source_resolver=session.source_binding).curve(value,context=context,observer=observer)
            assert after.sample_instants==before.sample_instants
            assert after.tick_sample_indices==before.tick_sample_indices
            np.testing.assert_allclose(after.geometry.lon_deg[0],before.geometry.lon_deg[0],rtol=0,atol=1e-11)
            np.testing.assert_allclose(after.geometry.lat_deg[0],before.geometry.lat_deg[0],rtol=0,atol=1e-11)


@pytest.mark.parametrize('fixture_name,raw_name', [
    ('horizons_comet_validation_50a4.json','50a4-raw-v2'),
    ('horizons_comet_validation_50a5c.json','50a5c-161p-raw'),
])
def test_real_offline_comet_kernel_routes_preserve_science(fixture_name, raw_name):
    """Captured SPK and fixture oracles; no acquisition or substituted resources."""
    from dataclasses import replace
    from astropy.time import Time
    import numpy as np
    from wenu.observer import Observer, DEFAULT_DATA_DIRECTORY, DEFAULT_EPHEMERIS
    from wenu.ephemeris import EphemerisStateRequest
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu.minor_body_ephemeris import SpiceMinorBodyKernel, SkyfieldMinorBodyStateSource
    from wenu.skyfield_ephemeris import SkyfieldEphemerisStateSource
    from wenu.sky.solar_system_points import SolarSystemPointLayer, EphemerisSourceBinding
    from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer
    from wenu.sky.solar_system_bodies import SolarSystemBodyDescriptor, SYMBOLIC_POINT, APPARENT_TRACK
    from tools.validate_50a2_asteroids import _solution
    from test_solar_system_tracks import CONTEXT, request
    fixture=json.loads((Path('tests/fixtures')/fixture_name).read_text())
    record=fixture['objects'][0];epoch=record['epochs'][0]
    data=Path(DEFAULT_DATA_DIRECTORY)
    path=data/'minor_bodies'/raw_name/record['spk']['filename']
    for required in (path,data/DEFAULT_EPHEMERIS):
        if not required.is_file():
            raise FileNotFoundError(f'offline comet acceptance requires {required}')
    assert sha256(path.read_bytes()).hexdigest()==record['spk']['sha256']
    key=record['primary_designation'].casefold()
    descriptor=SolarSystemBodyDescriptor(target=key,entity_key='comet_'+key,
        display_name=record['name'],selection_key=key,body_class='comet',
        physical_body_id=record['provider_spk_id'],canonical_designation=record['primary_designation'],
        iau_number=record['iau_number'],classifications=frozenset({'comet'}),
        capabilities=frozenset({SYMBOLIC_POINT,APPARENT_TRACK}),ephemeris_source_key='minor_body_spk')
    # Use the existing numerical fixture conversion, with explicit API target
    # mapping and only aliases actually present in the source fixture.
    solution=replace(_solution(record,fixture['authority']['horizons_version']),
        wenu_target=key,aliases=tuple(record.get('aliases',())))
    with Observer(location='La Ligua',time=epoch['calendar']+'Z') as observer:
        planetary=SkyfieldEphemerisStateSource.from_observer(observer)
        with SpiceMinorBodyKernel(path) as kernel:
            raw=SkyfieldMinorBodyStateSource.from_kernels(small_body_kernel=kernel,
                planetary_source=planetary,timescale=observer.timescale,
                solution=solution,model='Horizons '+solution.orbit_solution_id,
                provider_gas_tail_position_angles=tuple((e['calendar_utc'],e['horizons_psang_deg'])
                    for e in fixture.get('antisolar',{}).get('epochs',())))
            source=KernelEphemerisStateSource(raw)
            instant=Time(epoch['vector_jd_tdb'],format='jd',scale='tdb');instant.precision=9
            query=EphemerisStateRequest(key,descriptor.centre,'icrf',instant.isot,'tdb')
            before=raw.state(query);after=source.state(query)
            np.testing.assert_allclose(after.position,before.position,rtol=0,atol=1e-14)
            np.testing.assert_allclose(after.velocity,before.velocity,rtol=0,atol=1e-16)
            np.testing.assert_allclose(after.position,epoch['position_au'],rtol=0,atol=fixture['tolerances']['position_au'])
            np.testing.assert_allclose(after.velocity,epoch['velocity_au_per_day'],rtol=0,atol=fixture['tolerances']['velocity_au_per_day'])
            assert after.solution is before.solution is solution
            assert after.segment is before.segment
            assert {'A1','A2'}.issubset(dict(after.solution.model_parameters))
            context=replace(CONTEXT,evaluation_instant=epoch['calendar'],evaluation_time_scale='utc',
                observation=replace(CONTEXT.observation,instant=epoch['calendar']))
            raw_resolver=lambda d,o:EphemerisSourceBinding(raw,planetary)
            resolver=lambda d,o:EphemerisSourceBinding(source,planetary)
            point=SolarSystemPointLayer(descriptor,source_resolver=resolver).realize(context,observer)
            expected=SolarSystemPointLayer(descriptor,source_resolver=raw_resolver).realize(context,observer)
            np.testing.assert_allclose(point.lon_deg,expected.lon_deg,rtol=0,atol=1e-11)
            np.testing.assert_allclose(point.lat_deg,expected.lat_deg,rtol=0,atol=1e-11)
            assert abs(((point.lon_deg[0]-epoch['topocentric']['apparent_ra_deg']+180)%360)-180)<1e-5
            assert abs(point.lat_deg[0]-epoch['topocentric']['apparent_dec_deg'])<1e-5
            assert point.metadata['comet_tail_orientation_source']==expected.metadata['comet_tail_orientation_source']
            from wenu.charts.object_center import get_object_center
            center=get_object_center(descriptor,observer,source_resolver=resolver)
            expected_center=get_object_center(descriptor,observer,source_resolver=raw_resolver)
            assert center.key==key and len(center.geometry.lon_deg)==1
            np.testing.assert_allclose(center.geometry.lon_deg,expected_center.geometry.lon_deg,rtol=0,atol=1e-10)
            np.testing.assert_allclose(center.geometry.lat_deg,expected_center.geometry.lat_deg,rtol=0,atol=1e-10)
            value=request(descriptor=descriptor,start_instant=epoch['calendar']+'Z',sample_step_days=.5,tick_step_days=.75,tick_count=1)
            actual=SolarSystemTrackRealizer(source_resolver=resolver).curve(value,context=context,observer=observer)
            expected=SolarSystemTrackRealizer(source_resolver=raw_resolver).curve(value,context=context,observer=observer)
            assert actual.sample_instants==expected.sample_instants
            assert actual.tick_sample_indices==expected.tick_sample_indices
            np.testing.assert_allclose(actual.geometry.lon_deg[0],expected.geometry.lon_deg[0],rtol=0,atol=1e-11)
            np.testing.assert_allclose(actual.geometry.lat_deg[0],expected.geometry.lat_deg[0],rtol=0,atol=1e-11)


def test_ceres_manifest_preserves_frozen_facts_and_validates_identity(monkeypatch):
    from importlib.resources import files
    from dataclasses import asdict
    from wenu.sky import ceres
    document = json.loads(files('wenu.data').joinpath('ceres_solution_v1.json').read_text())
    expected = json.loads(json.dumps(asdict(ceres.CERES_SOLUTION)))
    assert document == {'schema_version': 1, 'solution': expected}
    fixture = json.loads(Path('tests/fixtures/horizons_asteroid_validation_50a2.json').read_text())
    record = fixture['objects'][0]
    for key in ('provider_spk_id','orbit_solution_id','solution_date','osculating_epoch'):
        assert document['solution'][key] == record[key]
    assert dict(ceres.CERES_SOLUTION.quality_fields) == record['quality_fields']
    class Resource:
        def joinpath(self, name):
            return self
        def read_text(self, **kwargs):
            return json.dumps(document)
    monkeypatch.setattr('importlib.resources.files', lambda name: Resource())
    document['solution']['provider_spk_id'] = '20000002'
    with pytest.raises(ValueError, match='differs from body identity'):
        ceres._load_solution()
    document['schema_version'] = 2
    with pytest.raises(ValueError, match='unsupported Ceres'):
        ceres._load_solution()


@pytest.mark.parametrize('numbered', [False, True])
def test_asteroid_session_point_and_track_consume_kernel_and_refuse(tmp_path, monkeypatch, numbered):
    _assert_minor_body_session_consumers(tmp_path, monkeypatch, numbered=numbered)


@pytest.mark.parametrize('comet', ['2P', '161P', 'C/2006 P1'])
def test_comet_session_point_track_symbols_consume_kernel_and_refuse(tmp_path, monkeypatch, comet):
    _assert_minor_body_session_consumers(tmp_path, monkeypatch, comet=comet)


def _assert_minor_body_session_consumers(tmp_path, monkeypatch, *, numbered=False, comet=None):
    """Synthetic SPK/observer inputs; real composition, kernel and light-time paths."""
    from dataclasses import replace
    from astropy.time import Time
    from astropy import units as u
    import numpy as np
    from wenu.ephemeris import EphemerisState, EphemerisStateRequest
    from wenu.ephemeris_state import KernelEphemerisStateSource
    from wenu.sky.solar_system_points import SolarSystemPointLayer, EphemerisSourceBinding
    from wenu.sky.solar_system_tracks import SolarSystemTrackRealizer
    from wenu_kernel.kernel import KernelSession
    from wenu_kernel.errors import UnsupportedCapability, ProviderEvaluationError
    from test_solar_system_tracks import RESOURCE, CONTEXT, ApparentRealizer, observer_state, sample_observer, request
    CONTEXT = replace(CONTEXT, evaluation_instant='2026-08-30T00:00:00', evaluation_time_scale='utc')
    directory = numbered_manifest_directory(tmp_path) if numbered else manifest_directory(tmp_path)
    if numbered:
        payload = b'DAF/synthetic numbered asteroid'
        (tmp_path/'79989.bsp').write_bytes(payload)
        path = tmp_path/'acquisition-report.json'
        doc = json.loads(path.read_text());doc['resources'][0]['sha256'] = sha256(payload).hexdigest()
        path.write_text(json.dumps(doc))
    target = 20079989 if numbered else 20000001
    selection = '79989' if numbered else '1'
    if comet is not None:
        target = {'2P':1000025, '161P':1000042, 'C/2006 P1':1002410}[comet]
        directory = comet_manifest_directory(tmp_path,
            designation='2P' if comet == 'C/2006 P1' else comet,
            target=str(target), name={'2P':'Encke','161P':'Hartley-IRAS','C/2006 P1':'McNaught'}[comet])
        path = directory/'acquisition-report.json'
        doc = json.loads(path.read_text());record=doc['resources'][0]
        record['actual_coverage']={'start_jd_tdb':2460000.5,'stop_jd_tdb':2470000.5}
        if comet == 'C/2006 P1':
            record['identity'].update(permanent_number=None,primary_designation='2006 P1',designation_class='C')
            record['solution'].update(primary_designation='2006 P1',aliases=['C/2006 P1','McNaught'])
        record['horizons_result'] = (record['solution']['primary_designation'] +
            '\nSoln.date: '+record['solution']['solution_date']+'\nsoln ref.= JPL#'+record['solution']['orbit_solution_id'])
        # Exact synthetic UTC samples for the unchanged source-owned hook.
        record['provider_gas_tail_position_angles']=[
            {'calendar_utc':(Time('2026-08-30T00:00:00',scale='utc')+u.day*offset).strftime('%Y-%m-%dT%H:%M:%S'),
             'position_angle_deg':65.412} for offset in request().sample_offsets_days]
        path.write_text(json.dumps(doc));selection=comet
    class Segment:
        center=10; frame_id=1; data_type=21
        start_jd=2460000.5; end_jd=2470000.5
        def at(self, time):
            if kernel._closed:
                raise ValueError('synthetic asteroid SPK is closed')
            angle = float(time.tdb)-2461282.5
            return SimpleNamespace(position=SimpleNamespace(au=(2*np.cos(angle),2*np.sin(angle),.2)),
                velocity=SimpleNamespace(au_per_d=(0.,0.,0.)))
        @property
        def spk_segment(self):
            return self
    segment=Segment();segment.target=target
    class Kernel:
        def __init__(self, path):
            nonlocal kernel
            kernel=self;self.path=path;self.segments=(segment,);self._closed=False;self.closes=0
        def close(self):
            self._closed=True;self.closes+=1
    kernel=None
    planetary=SimpleNamespace(resource=RESOURCE)
    planetary.state=lambda q: EphemerisState(q,((-.5,0.,0.) if comet else (0.,0.,0.)),(0.,0.,0.),'au','au/day',RESOURCE,q.target,'0')
    monkeypatch.setattr('wenu.minor_body_resources.SpiceMinorBodyKernel',Kernel)
    monkeypatch.setattr('wenu.minor_body_resources.SkyfieldEphemerisStateSource.from_observer',lambda observer:planetary)
    observer=SimpleNamespace(t_astropy=Time('2026-08-30T00:00:00',scale='utc'),
        timescale=SimpleNamespace(from_astropy=lambda t:SimpleNamespace(tdb=float(t.tdb.jd))))
    session=MinorBodyResourceSession(directory,observer)
    descriptor=session.collection.resolve(selection)
    binding=session.source_binding(descriptor,observer)
    assert isinstance(binding.target_source,KernelEphemerisStateSource)
    assert binding.observer_source is planetary
    assert session.source_binding(descriptor,observer).target_source is binding.target_source
    options=dict(observer_state_factory=observer_state,apparent_realizer=ApparentRealizer())
    raw_resolver=lambda d,o:EphemerisSourceBinding(binding.target_source.source,planetary)
    point=SolarSystemPointLayer(descriptor,source_resolver=session.source_binding,**options)
    track=SolarSystemTrackRealizer(source_resolver=session.source_binding,sample_observer_factory=sample_observer,**options)
    value=request(descriptor=descriptor)
    baseline=SolarSystemTrackRealizer(source_resolver=raw_resolver,sample_observer_factory=sample_observer,**options).curve(value,context=CONTEXT,observer=observer)
    p=point.realize(CONTEXT,observer)
    if comet is not None:
        assert p.metadata['comet_tail_orientation_source']=='provider PsAng'
        assert p.metadata['antisolar_position_angle_deg']==65.412
        original_state=binding.target_source.state(EphemerisStateRequest(
            descriptor.target,descriptor.centre,'icrf','2026-08-30T00:00:00','tdb'))
        assert original_state.solution is session.collection.solution_for(descriptor)
        assert original_state.solution.model_parameters==(('A1','radial'),('A2','transverse'))
        assert original_state.segment.target_id==target

    actual=track.curve(value,context=CONTEXT,observer=observer)
    np.testing.assert_allclose(actual.geometry.lon_deg[0],baseline.geometry.lon_deg[0],rtol=0,atol=1e-11)
    assert actual.sample_instants == baseline.sample_instants
    assert actual.tick_sample_indices == baseline.tick_sample_indices
    # Compare actual canonical pixels, including sample-derived symbols. The
    # apparent backend above is synthetic; this is a routing/output oracle.
    import matplotlib.pyplot as plt
    from matplotlib.image import imread
    from test_chart_request_tracks import request as chart_request
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.charts.request_tracks import configure_chart_request_track
    from wenu.charts.detail_application import composition_layer_options
    from wenu.charts.styles import PublicationStyle
    from wenu.charts.detail import ResolvedDetail
    from wenu.charts.context import Viewport, BoundaryKind
    from wenu.projections import StereographicProjection
    from wenu.rendering import MatplotlibRenderer
    projection=StereographicProjection()
    projected=projection.project_geometry(baseline.geometry)[0]
    cx,cy=float(np.mean(projected.x)),float(np.mean(projected.y))
    viewport=Viewport(cx-1.,cx+1.,cy-1.,cy+1.)
    composition=SimpleNamespace(style=PublicationStyle(),detail=ResolvedDetail(),
        context=SimpleNamespace(boundary_kind=BoundaryKind.RECTANGULAR,viewport=viewport))
    images=[]
    for routed in (False,True):
        sky=CelestialSphere(None)
        chart=replace(chart_request('regional'),solar_system_tracks=(value,),
            minor_body_descriptors=(descriptor,),minor_body_resource_directory=directory,
            solar_system_track_symbols='major',solar_system_track_labels='major')
        layer=configure_chart_request_track(sky,chart)
        owner=layer.track_realization.realizer
        owner.source_resolver=session.source_binding if routed else raw_resolver
        owner.observer_state_factory=observer_state
        owner.sample_observer_factory=sample_observer
        owner.apparent_realizer=ApparentRealizer()
        configured=composition_layer_options(composition,sky,reload_catalogues=False)
        if comet is not None:
            sky.add(SolarSystemPointLayer(descriptor,
                source_resolver=session.source_binding if routed else raw_resolver,**options))
            sky.solar_system_bodies[descriptor.selection_key]=sky.layers[-1]
            configured=composition_layer_options(composition,sky,reload_catalogues=False)

        figure,axes=plt.subplots(figsize=(4,3),dpi=90)
        try:
            sky.draw_chart(observer=observer,realization_context=CONTEXT,
                projection=projection,renderer=MatplotlibRenderer(axes),
                layer_options=configured.layer_options,viewport=viewport)
            if comet is not None:
                from wenu.sky.solar_system_track_layer import CometTrackSymbolLayer
                symbols=[x for x in sky.layers if isinstance(x,CometTrackSymbolLayer)]
                assert len(symbols)==value.tick_count+1
                for symbol in symbols:
                    geometry=symbol.realize(CONTEXT,observer)
                    assert geometry.metadata['comet_tail_orientation_source']=='provider PsAng'
                    assert geometry.metadata['antisolar_position_angle_deg']==65.412
            axes.set_axis_off()
            output=tmp_path/f'asteroid-{routed}.png';figure.savefig(output)
            images.append(imread(output))
        finally:
            plt.close(figure)
    np.testing.assert_array_equal(images[0],images[1])
    assert np.any(images[0][:,:,:3]<.5)
    if comet is not None:
        source=binding.target_source.source
        hook=source.apparent_gas_tail_position_angle_deg
        def refused_hook(**kwargs):
            raise ValueError('provider tail sample refused after warm use')
        source.apparent_gas_tail_position_angle_deg=refused_hook
        try:
            with pytest.raises(ValueError,match='provider tail sample refused'):
                point.realize(CONTEXT,observer)
            with pytest.raises(ValueError,match='provider tail sample refused'):
                symbols[0].realize(CONTEXT,observer)
        finally:
            source.apparent_gas_tail_position_angle_deg=hook
    original=KernelSession.evaluate;queries=[]
    def changed(s,q):
        queries.append(q);batch=original(s,q);row=batch.states[0];x,y,z=row.position_m
        return replace(batch,states=(replace(row,position_m=(-y,x,z)),))
    monkeypatch.setattr(KernelSession,'evaluate',changed)
    moved=point.realize(CONTEXT,observer)
    np.testing.assert_allclose(moved.lon_deg,(p.lon_deg+90)%360,rtol=0,atol=1e-9)
    moved_track=track.curve(value,context=CONTEXT,observer=observer)
    np.testing.assert_allclose(moved_track.geometry.lon_deg[0],(actual.geometry.lon_deg[0]+90)%360,rtol=0,atol=1e-9)
    assert queries and all(len(q.catalogue.resources)==2 for q in queries)
    def refuse(s,q):
        raise UnsupportedCapability('asteroid state refused')
    monkeypatch.setattr(KernelSession,'evaluate',refuse)
    with pytest.raises(UnsupportedCapability,match='asteroid state refused'):
        point.realize(CONTEXT,observer)
    with pytest.raises(UnsupportedCapability,match='asteroid state refused'):
        track.curve(value,context=CONTEXT,observer=observer)
    monkeypatch.setattr(KernelSession,'evaluate',original)
    from wenu.sky.solar_system_track_layer import SolarSystemTrackRealization
    shared=SolarSystemTrackRealization(value,realizer=track)
    shared.realize(CONTEXT,observer)
    session.close();session.close()
    assert kernel.closes==1
    with pytest.raises(ValueError,match='session is closed'):
        point.realize(CONTEXT,observer)
    with pytest.raises(ValueError,match='session is closed'):
        shared.realize(CONTEXT,observer)
    with pytest.raises(ProviderEvaluationError) as closed:
        binding.target_source.state(EphemerisStateRequest(
            descriptor.target,descriptor.centre,'icrf','2026-08-30T00:00:00','tdb'))
    assert 'SPK is closed' in str(closed.value.__cause__)


def comet_manifest_directory(
    tmp_path, *, designation="2P", target="1000025", name="Encke",
    solution_id="K273/14", aliases=None,
):
    payload = b"DAF/fake Encke kernel"
    (tmp_path / "encke.bsp").write_bytes(payload)
    record = {
        "key": "2p",
        "filename": "encke.bsp",
        "sha256": sha256(payload).hexdigest(),
        "spk_file_id": target,
        "actual_coverage": {
            "start_jd_tdb": 2461327.5,
            "stop_jd_tdb": 2461567.5,
        },
        "horizons_result": (
            "2P/Encke\nSoln.date: 2026-Sep-08_14:23:39\n"
            "soln ref.= JPL#K273/14"
        ),
        "identity": {
            "permanent_number": int(designation[:-1]),
            "primary_designation": designation,
            "designation_class": designation[-1],
            "name": name,
            "object_class": "comet",
            "provider_spk_id": target,
            "classifications": ["comet", "periodic_comet"],
        },
        "solution": {
            "provider": "NASA/JPL Horizons API",
            "service_version": "1.2",
            "object_class": "comet",
            "primary_designation": designation,
            "horizons_command": "90000091;",
            "provider_spk_id": target,
            "orbit_solution_id": solution_id,
            "solution_date": "2026-Sep-08_14:23:39",
            "osculating_epoch": "2459936.5 TDB",
            "reference_system": "J2000 ecliptic and equinox",
            "aliases": aliases or [f"{designation}/{name}", name],
            "model_parameters": {"A1": "radial", "A2": "transverse"},
        },
    }
    (tmp_path / "acquisition-report.json").write_text(
        json.dumps({"resources": [record]}), encoding="utf-8"
    )
    return tmp_path


def test_collection_preserves_typed_encke_identity_and_solution(tmp_path):
    collection = MinorBodyResourceCollection(comet_manifest_directory(tmp_path))

    encke = collection.resolve(" 2P/ENCKE ")

    assert collection.resolve("2p") is encke
    assert collection.resolve("encke") is encke
    assert encke.selection_key == "2p"
    assert encke.target == "2p"
    assert encke.entity_key == "comet_2p"
    assert encke.body_class == "comet"
    assert encke.canonical_designation == "2P/Encke"
    assert encke.physical_body_id == "1000025"
    solution = collection.solution_for(encke)
    assert solution.primary_designation == "2P"
    assert solution.horizons_command == "90000091;"
    assert solution.orbit_solution_id == "K273/14"
    assert set(dict(solution.model_parameters)) == {"A1", "A2"}


def test_collection_reconstructs_provisional_comet_class_prefix(tmp_path):
    directory = comet_manifest_directory(tmp_path)
    manifest = directory / "acquisition-report.json"
    document = json.loads(manifest.read_text(encoding="utf-8"))
    record = document["resources"][0]
    record["key"] = "C/2006 P1"
    record["identity"].update({
        "permanent_number": None,
        "primary_designation": "2006 P1",
        "designation_class": "C",
        "name": "McNaught",
    })
    record["solution"]["primary_designation"] = "2006 P1"
    record["solution"]["aliases"] = [
        "2006 P1", "C/2006 P1", "C/2006 P1 (McNaught)",
    ]
    manifest.write_text(json.dumps(document), encoding="utf-8")

    collection = MinorBodyResourceCollection(directory)
    mcnaught = collection.resolve("C/2006 P1")

    assert collection.resolve("C/2006 P1 (McNaught)") is mcnaught
    assert mcnaught.selection_key == "c/2006 p1"
    assert mcnaught.canonical_designation == "C/2006 P1/McNaught"
    assert collection.solution_for(mcnaught).primary_designation == "2006 P1"


def test_collection_rejects_receipt_prefix_in_comet_solution_id(tmp_path):
    directory = comet_manifest_directory(
        tmp_path, solution_id="JPL#K273/14"
    )

    with pytest.raises(ValueError, match="excludes the Horizons JPL# prefix"):
        MinorBodyResourceCollection(directory)


def test_collection_does_not_treat_2p_as_asteroid_2(tmp_path):
    collection = MinorBodyResourceCollection(comet_manifest_directory(tmp_path))

    with pytest.raises(KeyError, match="no installed object"):
        collection.resolve("2")


def test_session_opens_encke_once_and_checks_comet_coverage(
    tmp_path, monkeypatch
):
    _, source, kernels, closes = install_fakes(
        monkeypatch,
        target=1000025,
        coverage=(2461327.5, 2461567.5),
    )
    observer = SimpleNamespace(timescale=object())
    session = MinorBodyResourceSession(
        comet_manifest_directory(tmp_path), observer
    )
    descriptor = session.collection.resolve("2P")

    assert session.source_binding(descriptor, observer).target_source is source
    assert session.source_binding(descriptor, observer).target_source is source
    assert len(kernels) == 1
    session.close()
    assert closes == kernels


def test_collection_resolves_second_installed_comet_without_runtime_branch(
    tmp_path,
):
    collection = MinorBodyResourceCollection(comet_manifest_directory(
        tmp_path,
        designation="161P",
        target="1000042",
        name="Hartley-IRAS",
        solution_id="71",
        aliases=["161P/Hartley-IRAS", "Hartley-IRAS"],
    ))

    hartley = collection.resolve("161P/Hartley-IRAS")

    assert collection.resolve("hartley-iras") is hartley
    assert hartley.selection_key == "161p"
    assert hartley.entity_key == "comet_161p"
    assert hartley.canonical_designation == "161P/Hartley-IRAS"
    assert hartley.physical_body_id == "1000042"
    assert collection.solution_for(hartley).orbit_solution_id == "71"


def test_generic_comet_installer_publishes_verified_fixture_atomically(
    tmp_path, monkeypatch,
):
    raw = tmp_path / "raw"
    raw.mkdir()
    spk = raw / "161p-hartley-iras.bsp"
    spk.write_bytes(b"DAF/accepted 161P")
    topocentric = raw / "horizons-topocentric.json"
    topocentric.write_text(json.dumps({
        "result": (
            "161P/Hartley-IRAS\nSoln.date: 2026-Sep-08_09:12:21\n"
            "soln ref.= JPL#71"
        ),
    }), encoding="utf-8")
    sbdb = raw / "sbdb-161p.json"
    sbdb.write_text("{}", encoding="utf-8")
    vectors = raw / "horizons-vectors.json"
    vectors.write_text("{}", encoding="utf-8")
    geocentric = raw / "horizons-geocentric.json"
    geocentric.write_text("{}", encoding="utf-8")
    source_digests = {
        path.name: sha256(path.read_bytes()).hexdigest()
        for path in (sbdb, vectors, geocentric, topocentric)
    }
    fixture = tmp_path / "fixture.json"
    fixture.write_text(json.dumps({
        "authority": {
            "horizons_api": "NASA/JPL Horizons API",
            "horizons_version": "1.2",
        },
        "objects": [{
            "aliases": ["161P/Hartley-IRAS", "Hartley-IRAS"],
            "class": "comet",
            "epochs": [{"calendar": "2026-09-01T00:00:00"}],
            "horizons_command": "90001107;",
            "iau_number": 161,
            "key": "161p-hartley-iras",
            "model_parameters": [
                {"name": "A1", "value": "1.1e-8"},
                {"name": "A2", "value": "-3.3e-10"},
            ],
            "name": "Hartley-IRAS",
            "orbit_solution_id": "71",
            "osculating_epoch": "2455861.5 TDB",
            "primary_designation": "161P",
            "provider_spk_id": "1000042",
            "quality_fields": {"condition_code": "0"},
            "reference_system": "J2000 ecliptic and equinox",
            "solution_date": "2026-09-08 09:12:21",
            "source_evidence_sha256": source_digests,
            "spk": {
                "coverage_end_jd_tdb": 2461374.5,
                "coverage_start_jd_tdb": 2461254.5,
                "filename": spk.name,
                "segment_centre_id": 10,
                "segment_type": 21,
                "sha256": sha256(spk.read_bytes()).hexdigest(),
            },
        }],
        "antisolar": {
            "epochs": [{
                "calendar_utc": "2026-09-01T00:00:00",
                "horizons_psang_deg": 269.947,
            }],
            "source_evidence_sha256": {},
            "tolerances": {"antisolar_position_angle_deg": 0.01},
        },
        "tolerances": {"direction_deg": 1e-5},
    }), encoding="utf-8")

    segment = SimpleNamespace(
        target=1000042, center=10, frame_id=1, data_type=21,
        start_jd=2461254.5, end_jd=2461374.5,
    )
    class Kernel:
        def __init__(self, path):
            assert path == spk
            self.segments = (segment,)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
    monkeypatch.setattr(install_comet_resource, "SpiceMinorBodyKernel", Kernel)
    output = tmp_path / "installed"

    manifest = install_comet_resource.install(fixture, raw, output)
    collection = MinorBodyResourceCollection(output)
    hartley = collection.resolve("Hartley-IRAS")

    assert manifest == output / "acquisition-report.json"
    assert collection.resolve("161P") is hartley
    assert collection.resolve("161P/Hartley-IRAS") is hartley
    assert collection.solution_for(hartley).orbit_solution_id == "71"
    record = collection.record_for(hartley)
    assert record["provider_gas_tail_position_angles"] == [{
        "calendar_utc": "2026-09-01T00:00:00",
        "position_angle_deg": 269.947,
    }]


@pytest.mark.parametrize(
    ("value", "designation_class", "number"),
    (("2P", "P", 2), ("3D", "D", 3), ("1I", "I", 1)),
)
def test_numbered_comet_designations_preserve_class(value, designation_class, number):
    designation = parse_comet_designation(value)

    assert designation.canonical == value
    assert designation.designation_class == designation_class
    assert designation.permanent_number == number


@pytest.mark.parametrize("value", ("C/2020 F3", "P/2011 NO1", "C/2020 F3-A"))
def test_provisional_comet_designations_preserve_structure(value):
    designation = parse_comet_designation(value.lower())

    assert designation.canonical == value
    assert designation.provisional_year is not None


def test_comet_designation_classes_do_not_collapse_to_one_integer():
    assert parse_comet_designation("2P") != parse_comet_designation("2D")
    with pytest.raises(ValueError, match="invalid comet designation"):
        parse_comet_designation("2")

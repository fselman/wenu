"""Object-independent nominal astrometric engine and isolated SDK composition."""
from dataclasses import replace
from pathlib import Path
import inspect
import subprocess
import sys
from math import atan2, isclose

import pytest
from wenu.astrometric_state import RectilinearAstrometricProvider, SpaceMotionRow
from wenu_kernel import Kernel
from wenu_kernel.records import AccuracyRequest, StateQuery, SessionPolicy, TimePoint


def mixed_provider(provider_class, row_class, representation="direction", scale="tcb", angular=False):
    """Constructed inputs for four families, with no catalogue-specific fixture."""
    from wenu_kernel.records import (
        CatalogueRef, CatalogueSnapshot, ExternalId, ModelAdmission, ModelRef,
        ObjectKey, ObjectRecord, ProviderDescriptor, ProviderKey, ReferenceSpec,
        ResourceRef, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
    )
    epoch = TimePoint(2451545, 0, scale)
    span = TimeSpan(TimePoint(2451544, 0, scale), TimePoint(2451546, 0, scale))
    if angular:
        span = TimeSpan(TimePoint(2451545-18262500,0,scale),TimePoint(2451545+18262500,0,scale))
    cartesian = representation == 'cartesian'
    key = ProviderKey('constructed-mixed-astrometry'+('.angular' if angular else '.pv' if cartesian else ''), '1')
    resource = ResourceRef('constructed-si-solutions', '1', 'a'*64, span,
                           'synthetic nominal domain', ('Constructed test inputs',))
    kinds = ('star', 'open-cluster', 'planetary-nebula', 'supernova-remnant')
    keys = tuple(ObjectKey('constructed:'+kind) for kind in kinds)
    ref = CatalogueRef(key, (resource,), 'b'*64)
    model = ModelRef('constructed-angular' if angular else 'constructed-rectilinear', '1', 'c'*64, (resource,))
    frame = ReferenceSpec('icrs','solar-system-barycenter','nominal-astrometric',
                          representation,'m,m/s' if cartesian else 'rad',
                          'synthetic normalized tangent angular approximation' if angular else 'synthetic no additional light time')
    caps = (('cartesian_state','batch_evaluation') if cartesian else
            ('epoch_direction','batch_evaluation','direction_reuse_bound'))
    objects = tuple(ObjectRecord(k,(ExternalId('constructed','1',kind),),kind,
        (epoch,),caps,('Constructed test inputs',)) for k,kind in zip(keys,kinds))
    catalogue = CatalogueSnapshot(ref, objects)
    admission = ModelAdmission(ref, model, frame, keys, caps, span)
    descriptor = ProviderDescriptor(key, (ref,), (admission,), 'synthetic multi-family provider')
    evidence = UncertaintyEvidence(
        UncertaintyChannel('not_evaluated',None,'rad','source measurement'),
        UncertaintyChannel('not_evaluated',None,'rad','nominal model'),
        UncertaintyChannel('bounded',2**-40,'rad','angular_separation'))
    reuse = ModelRef('constructed-cone','1','d'*64,(resource,))
    rows = [(k,row_class(kind,epoch,(1.,0.,0.) if angular else (1e12,0.,0.),
                         (0.,2e-12,1e-12) if angular else (1000.,2000.,0.),None))
            for k,kind in zip(keys,kinds)]
    velocity_evidence = None
    if cartesian:
        def unknown(unit):
            return UncertaintyEvidence(*(UncertaintyChannel('not_evaluated',None,unit,meaning)
                for meaning in ('source measurement','nominal model','euclidean_norm')))
        evidence,velocity_evidence,reuse = unknown('m'),unknown('m/s'),None
    return provider_class(rows,descriptor=descriptor,catalogue=catalogue,
        admission=admission,evidence=evidence,reuse_method=reuse,velocity_evidence=velocity_evidence)


def test_one_provider_propagates_all_object_types_without_type_dispatch():
    # Protect type-dependent numerical dispatch and loss of source/anchor identity.
    p = mixed_provider(RectilinearAstrometricProvider, SpaceMotionRow)
    a = p.describe().admissions[0]
    assert {row.semantic_type for row in p.catalogue(a.catalogue).objects} == {
        'star','open-cluster','planetary-nebula','supernova-remnant'}
    time = TimePoint(2451545, 1/86400, 'tcb')
    q = StateQuery(a.catalogue,a.model,tuple(reversed(a.objects)),(time,),a.reference,AccuracyRequest())
    with Kernel(references=(a.reference,)) as kernel:
        kernel.register(p,ownership='owned')
        with kernel.open_session(SessionPolicy((a.catalogue,))) as session:
            states = session.evaluate(q).states
    expected = atan2(2000.,1e12+1000.)
    assert [state.object_key for state in states] == list(reversed(a.objects))
    assert len({state.vector for state in states}) == 1
    for state in states:
        assert isclose(atan2(state.vector[1],state.vector[0]),expected,rel_tol=1e-15)
        assert state.time == state.anchor_time == time
        assert state.source_epoch == TimePoint(2451545,0,'tcb')
        assert state.evidence.physical_model.status == 'not_evaluated'


def test_generic_engine_runs_without_wenu_catalogues_or_scientific_dependencies(tmp_path):
    # The ordinary Wenu facade remains broad. Load only this engine and the
    # accepted SDK under -I -S; no ambient Wenu/Astropy/NumPy can satisfy imports.
    import wenu_kernel
    core = Path(__file__).resolve().parents[1]/'src/wenu/astrometric_state.py'
    # Keep only the accepted SDK in the injected path. A legacy pathlib
    # backport there must not shadow the interpreter's standard library.
    import shutil
    sdk_root = tmp_path/'sdk-root'
    shutil.copytree(Path(wenu_kernel.__file__).resolve().parent, sdk_root/'wenu_kernel',
                    ignore=shutil.ignore_patterns('__pycache__'))
    (sdk_root/'pathlib.py').write_text("raise ImportError('ambient pathlib shadow must never load')\n")
    script = '''
import sys,importlib.util
import pathlib  # Resolve stdlib before adding a caller-supplied SDK path.
sys.path.insert(0,sys.argv[2])
spec=importlib.util.spec_from_file_location('isolated_astrometry',sys.argv[1])
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
exec(sys.argv[3])
p=mixed_provider(m.RectilinearAstrometricProvider,m.SpaceMotionRow)
from wenu_kernel import Kernel
from wenu_kernel.records import StateQuery,TimePoint,AccuracyRequest,SessionPolicy
a=p.describe().admissions[0]
q=StateQuery(a.catalogue,a.model,a.objects,(TimePoint(2451545,0,'tcb'),),a.reference,AccuracyRequest())
with Kernel(references=(a.reference,)) as k:
    k.register(p,ownership='owned')
    with k.open_session(SessionPolicy((a.catalogue,))) as s: assert len(s.evaluate(q).states)==4
p=mixed_provider(m.RectilinearAstrometricProvider,m.SpaceMotionRow,'cartesian')
a=p.describe().admissions[0]
q=StateQuery(a.catalogue,a.model,a.objects,(TimePoint(2451545,.1,'tcb'),),a.reference,
             AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
with Kernel(references=(a.reference,)) as k:
    k.register(p,ownership='owned')
    with k.open_session(SessionPolicy((a.catalogue,))) as s:
        batch=s.evaluate(q)
        assert all(row.velocity_available for row in batch.states)
boundary_path=pathlib.Path(sys.argv[1]).with_name('astrometric_coordinates.py')
bspec=importlib.util.spec_from_file_location('isolated_conventions',boundary_path)
b=importlib.util.module_from_spec(bspec);sys.modules[bspec.name]=b;bspec.loader.exec_module(b)
adapter=b.TcbTdbAdapter(a.coverage)
receipts=tuple(adapter.convert(t,'tdb') for t in q.times)
result=b.convert_barycentric_batch(batch,admission=a,
    source_coordinate_scale='tcb',time_admission=adapter.describe(),conversions=receipts)
assert len(result.states)==4
assert not any(n.split('.')[0] in ('wenu','astropy','numpy') for n in sys.modules)
'''
    result = subprocess.run([sys.executable,'-I','-S','-c',script,str(core),
        str(sdk_root),inspect.getsource(mixed_provider)],
        cwd=tmp_path,text=True,capture_output=True)
    assert result.returncode == 0, result.stdout+result.stderr


def test_generic_core_rejects_inconsistent_admission_before_publication():
    p = mixed_provider(RectilinearAstrometricProvider, SpaceMotionRow)
    kwargs = dict(descriptor=p.describe(),catalogue=p._catalogue,admission=p._admission,
                  evidence=p._evidence,reuse_method=p._reuse_method)
    with pytest.raises(ValueError):
        RectilinearAstrometricProvider(tuple(p._lookup.items())[:-1],**kwargs)
    with pytest.raises(ValueError):
        RectilinearAstrometricProvider(tuple(p._lookup.items()),
            **dict(kwargs,evidence=replace(p._evidence,numerical=replace(p._evidence.numerical,value=0.))))


def test_generic_mixed_provider_passes_shipped_conformance():
    import io, unittest
    from wenu_kernel.conformance import ProviderCase, ProviderActivity, provider_suite
    def factory():
        p=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow)
        a=p.describe().admissions[0]
        q=StateQuery(a.catalogue,a.model,a.objects,(TimePoint(2451545,0,'tcb'),
            TimePoint(2451545,.01,'tcb')),a.reference,AccuracyRequest())
        probe=replace(q,times=(TimePoint(2451545,.1,'tcb'),))
        counts=dict(evaluate=0,certify=0,close=0)
        evaluate,certify,close=p.evaluate,p.certify,p.close
        def measured(q): counts['evaluate']+=1;return evaluate(q)
        def certified(q,a): counts['certify']+=1;return certify(q,a)
        def closed(): counts['close']+=1;return close()
        p.evaluate,p.certify,p.close=measured,certified,closed
        # Inputs are frozen records/tuples and constructor copies its row mapping.
        return ProviderCase(p,q,probe,
            lambda:ProviderActivity(counts['evaluate'],counts['certify'],counts['close']),
            lambda:None,replace(q,evaluation_policy='bounded_reuse',accuracy=AccuracyRequest(angular_rad=1e-5)))
    result=unittest.TextTestRunner(stream=io.StringIO()).run(provider_suite(factory,name='MixedAstrometry'))
    assert result.wasSuccessful(),result.errors+result.failures
    assert result.testsRun==8 and not result.skipped


def test_generic_core_owns_domain_and_copied_si_row_validation():
    from wenu.astrometric_state import validate_space_motion_domain
    from wenu_kernel.records import TimeSpan
    epoch=TimePoint(2451545,0,'tcb')
    span=TimeSpan(TimePoint(2451544,0,'tcb'),TimePoint(2451546,0,'tcb'))
    position=[10.,0.,0.];velocity=[0.,1.,0.]
    row=SpaceMotionRow('constructed',epoch,position,velocity,None)
    position[0]=999.;velocity[1]=999.
    assert row.position_m==(10.,0.,0.) and row.velocity_m_s==(0.,1.,0.)
    validate_space_motion_domain(row,span)
    with pytest.raises(ValueError,match='singular'):
        validate_space_motion_domain(replace(row,velocity_m_s=(-1.,0.,0.)),span)
    with pytest.raises(ValueError,match='scale'):
        validate_space_motion_domain(replace(row,source_epoch=replace(epoch,scale='tt')),span)


def test_shared_cartesian_state_preserves_distance_velocity_provenance_and_exact_cache():
    from decimal import Decimal, localcontext
    from wenu_kernel.records import CartesianState
    p=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow,'cartesian')
    a=p.describe().admissions[0]
    times=(TimePoint(2451545,-.25,'tcb'),TimePoint(2451545,.125,'tcb'))
    q=StateQuery(a.catalogue,a.model,tuple(reversed(a.objects)),times,a.reference,
                 AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
    calls=[];evaluate=p.evaluate
    def counted(q): calls.append(q);return evaluate(q)
    p.evaluate=counted
    with Kernel(references=(a.reference,)) as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((a.catalogue,))) as session:
            result=session.evaluate(q)
            assert session.evaluate(q) is result and len(calls)==1
            for state in result.states:
                with localcontext() as context:
                    context.prec=80
                    dt=Decimal(state.time.jd2)*Decimal(86400)
                    expected=tuple(float(Decimal(x)+dt*Decimal(v))
                        for x,v in zip((1e12,0.,0.),(1000.,2000.,0.)))
                assert type(state) is CartesianState
                assert state.position_m==expected and state.velocity_m_s==(1000.,2000.,0.)
                assert state.velocity_available
                assert state.source_epoch==TimePoint(2451545,0,'tcb')
                assert state.anchor_time==state.time
                assert state.position_evidence.numerical.status=='not_evaluated'
                assert state.velocity_evidence.physical_model.status=='not_evaluated'
            assert [(s.time,s.object_key) for s in result.states]==[(t,k) for t in times for k in reversed(a.objects)]
            assert result.states[0].position_m!=result.states[4].position_m
            assert result.states[0].position_m[0]>1e11  # no normalization/range loss


def test_cartesian_refuses_unadmitted_bounds_reuse_wrong_scale_and_preserves_atomic_failure():
    from wenu_kernel.errors import KernelError
    p=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow,'cartesian')
    a=p.describe().admissions[0]
    q=StateQuery(a.catalogue,a.model,a.objects,(TimePoint(2451545,0,'tcb'),),a.reference,
        AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
    for invalid in (replace(q,accuracy=AccuracyRequest(position_m=1.,metric='euclidean_norm')),
                    replace(q,accuracy=AccuracyRequest(velocity_m_s=1.,metric='euclidean_norm')),
                    replace(q,accuracy=AccuracyRequest(angular_rad=1e-5)),
                    replace(q,evaluation_policy='bounded_reuse'),
                    replace(q,times=(TimePoint(2451545,0,'tt'),)),
                    replace(q,times=(TimePoint(2451548,0,'tcb'),))):
        assert not p.supports(invalid).supported
    with pytest.raises(KernelError): p.certify(q,None)
    key=a.objects[-1];row=p._lookup[key]
    # Constructed fault, never a zero-velocity replacement for absent RV.
    p._lookup[key]=replace(row,position_m=None,velocity_m_s=None,unavailable_reason='missing rv')
    with pytest.raises(KernelError): p.evaluate(q)
    p._lookup[key]=row
    assert len(p.evaluate(q).states)==4


def test_shared_cartesian_provider_passes_shipped_conformance():
    import io,unittest
    from wenu_kernel.conformance import ProviderCase,ProviderActivity,provider_suite
    def factory():
        p=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow,'cartesian')
        a=p.describe().admissions[0]
        q=StateQuery(a.catalogue,a.model,a.objects,(TimePoint(2451545,0,'tcb'),TimePoint(2451545,.01,'tcb')),
            a.reference,AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
        probe=replace(q,times=(TimePoint(2451545,.1,'tcb'),))
        counts=dict(evaluate=0,close=0);evaluate,close=p.evaluate,p.close
        def measured(q):counts['evaluate']+=1;return evaluate(q)
        def closed():counts['close']+=1;return close()
        p.evaluate,p.close=measured,closed
        return ProviderCase(p,q,probe,lambda:ProviderActivity(counts['evaluate'],0,counts['close']),lambda:None)
    result=unittest.TextTestRunner(stream=io.StringIO()).run(provider_suite(factory,name='CartesianAstrometry'))
    assert result.wasSuccessful(),result.errors+result.failures
    assert result.testsRun==8


def test_cartesian_and_direction_bindings_coexist_without_cross_evaluation():
    direction=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow)
    cartesian=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow,'cartesian')
    da,ca=(p.describe().admissions[0] for p in (direction,cartesian))
    assert da.objects==ca.objects
    calls=[];original=direction.evaluate
    def counted(q):calls.append(q);return original(q)
    direction.evaluate=counted
    time=(TimePoint(2451545,.1,'tcb'),)
    dq=StateQuery(da.catalogue,da.model,da.objects,time,da.reference,AccuracyRequest())
    cq=StateQuery(ca.catalogue,ca.model,ca.objects,time,ca.reference,AccuracyRequest(metric='euclidean_norm'))
    with Kernel(references=(da.reference,ca.reference)) as kernel:
        for p in (direction,cartesian):kernel.register(p,ownership='owned')
        with kernel.open_session(SessionPolicy((da.catalogue,ca.catalogue))) as session:
            first=session.evaluate(cq)
            assert calls==[]
            assert session.evaluate(dq).states[0].vector
            assert len(calls)==1 and session.evaluate(cq) is first


# Convention-boundary coverage extends the closest existing Cartesian batch,
# independent Decimal PV, immutable identity and isolated-module cases above.
def _assert_barycentric_time_reference(adapter, time):
    from decimal import Decimal, localcontext
    from wenu_kernel.time import TimeService
    receipt = TimeService((adapter,), admissions=(adapter.describe(),)).convert(
        time, adapter.describe().target_scale)
    with localcontext() as ctx:
        ctx.prec = 90
        day = Decimal(time.jd1) + Decimal(time.jd2)
        lb, t0 = Decimal('1.550519768e-8'), Decimal('2443144.5003725')
        offset = Decimal('-0.0000655') / Decimal(86400)
        expected = (day-lb*(day-t0)+offset if time.scale=='tcb'
                    else (day-lb*t0-offset)/(1-lb))
        actual = Decimal(receipt.target.jd1)+Decimal(receipt.target.jd2)
        assert abs(actual-expected)*Decimal(86400) <= Decimal(receipt.numerical_error_s)
    return receipt


@pytest.mark.parametrize('scale', ['tcb','tdb'])
@pytest.mark.parametrize('day,small', [(1000000,-.5),(2443145,-.4996275),
    (2451545,0.),(2462503,.49999999999999994),(4000000,-.125)])
def test_barycentric_time_matches_independent_decimal_and_erfa(scale, day, small):
    import erfa
    from math import fsum
    from wenu.astrometric_coordinates import TcbTdbAdapter
    from wenu_kernel.records import TimeSpan
    time=TimePoint(day,small,scale)
    adapter=TcbTdbAdapter(TimeSpan(TimePoint(day-1,0,scale),TimePoint(day+1,0,scale)))
    receipt=_assert_barycentric_time_reference(adapter,time)
    oracle=(erfa.tcbtdb if scale=='tcb' else erfa.tdbtcb)(day,small)
    # Independent ERFA uses binary64 defining constants, not our exact decimals.
    assert abs(fsum((receipt.target.jd1-oracle[0],receipt.target.jd2,-oracle[1])))*86400 < 1e-8
    assert -0.5 <= receipt.target.jd2 < 0.5
    assert receipt.source is time and receipt.target.scale!=time.scale
    assert receipt.numerical_error_s <= adapter.describe().maximum_error_s


def test_barycentric_time_admission_boundaries_and_corruption_detection(monkeypatch):
    import wenu.astrometric_coordinates as boundary
    from math import nextafter, inf
    from wenu_kernel.records import TimeSpan
    from wenu_kernel.time import TimeService
    from wenu_kernel.errors import KernelError
    start,stop=TimePoint(2451545,-.5,'tcb'),TimePoint(2451545,.25,'tcb')
    adapter=boundary.TcbTdbAdapter(TimeSpan(start,stop))
    for time in (start,stop):_assert_barycentric_time_reference(adapter,time)
    for time in (TimePoint(start.jd1-1,nextafter(.5,-inf),'tcb'),
                 TimePoint(stop.jd1,nextafter(stop.jd2,inf),'tcb')):
        with pytest.raises(KernelError):adapter.convert(time,'tdb')
    with pytest.raises(KernelError):TimeService((adapter,))
    with pytest.raises(KernelError):TimeService().convert(start,'tdb')
    with pytest.raises(KernelError):adapter.convert(replace(start,scale='tt'),'tdb')
    with pytest.raises(KernelError):adapter.convert(start,'tt')
    with pytest.raises(KernelError):boundary.TcbTdbAdapter(replace(adapter.describe().validity,
        start=replace(start,scale='tt'),stop=replace(stop,scale='tt')))
    _assert_barycentric_time_reference(adapter,stop)
    monkeypatch.setattr(boundary,'_LB',0)  # deliberate scale relabelling fault
    with pytest.raises(AssertionError):_assert_barycentric_time_reference(adapter,stop)


def _converted_mixed_batch(scale="tcb"):
    from wenu.astrometric_coordinates import TcbTdbAdapter,convert_barycentric_batch
    from wenu_kernel.time import TimeService
    p=mixed_provider(RectilinearAstrometricProvider,SpaceMotionRow,'cartesian',scale)
    a=p.describe().admissions[0]
    q=StateQuery(a.catalogue,a.model,tuple(reversed(a.objects)),
        (TimePoint(2451545,.125,scale),TimePoint(2451545,-.25,scale)),a.reference,
        AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
    with Kernel(references=(a.reference,)) as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((a.catalogue,))) as session:batch=session.evaluate(q)
    adapter=TcbTdbAdapter(a.coverage)
    service=TimeService((adapter,),admissions=(adapter.describe(),))
    receipts=tuple(service.convert(t,adapter.describe().target_scale) for t in q.times)
    converted=convert_barycentric_batch(batch,admission=a,source_coordinate_scale=scale,time_admission=adapter.describe(),conversions=receipts)
    return batch,a,receipts,converted


@pytest.mark.parametrize('scale',['tcb','tdb'])
def test_barycentric_scaling_preserves_actual_kernel_batch_evidence_and_order(scale):
    from decimal import Decimal,localcontext
    from dataclasses import FrozenInstanceError
    batch,a,receipts,converted=_converted_mixed_batch(scale)
    assert converted.original is batch and converted.admission is a
    assert converted.time_admission.validity==a.coverage
    assert len(converted.states)==8
    for original,state in zip(batch.states,converted.states):
        assert state.original is original
        assert state.time in tuple(r.target for r in receipts)
        assert state.coordinate_scale!=scale
        assert state.velocity_m_s is original.velocity_m_s
        assert state.original.source_epoch==TimePoint(2451545,0,scale)
        assert state.original.position_evidence.physical_model.status=='not_evaluated'
        with localcontext() as ctx:
            ctx.prec=90
            for x,y,error in zip(original.position_m,state.position_m,state.position_rounding_m):
                factor=1-Decimal('1.550519768e-8')
                exact=Decimal(x)*(factor if scale=='tcb' else 1/factor)
                assert abs(Decimal(y)-exact) <= Decimal(error)
        assert state.position_m!=original.position_m
    with pytest.raises(FrozenInstanceError):converted.states[0].position_m=(0,0,0)
    assert [s.original.object_key for s in converted.states]==list(batch.query.objects)*2


def test_barycentric_batch_refuses_wrong_bindings_partial_and_warm_faults():
    from wenu.astrometric_coordinates import convert_barycentric_batch
    from wenu_kernel.errors import KernelError
    batch,a,receipts,converted=_converted_mixed_batch()
    def run(b=batch,admission=a,scale='tcb',conversions=receipts,time_admission=converted.time_admission):
        return convert_barycentric_batch(b,admission=admission,
            source_coordinate_scale=scale,time_admission=time_admission,conversions=conversions)
    model=replace(a.model,configuration_digest='f'*64)
    faults=[lambda:run(admission=replace(a,model=model)),
        lambda:run(admission=replace(a,reference=replace(a.reference,origin_id='earth'))),
        lambda:run(admission=replace(a,catalogue=replace(a.catalogue,membership_digest='f'*64))),
        lambda:run(time_admission=replace(converted.time_admission,model=model)),
        lambda:run(time_admission=replace(converted.time_admission,validity=replace(
            a.coverage,stop=TimePoint(2451545,0,'tcb')))),
        lambda:run(scale='tdb'),lambda:run(scale='tt'),lambda:run(conversions=receipts[:-1]),
        lambda:run(conversions=tuple(reversed(receipts))),
        lambda:run(conversions=(replace(receipts[0],model=model),receipts[1])),
        lambda:run(conversions=(replace(receipts[0],numerical_error_s=0.),receipts[1])),
        lambda:run(replace(batch,states=batch.states[:-1])),
        lambda:run(replace(batch,states=tuple(reversed(batch.states)))),
        lambda:run(replace(batch,states=(replace(batch.states[0],velocity_m_s=None,
            velocity_evidence=None),*batch.states[1:]))),
        lambda:run(replace(batch,states=(replace(batch.states[0],anchor_time=batch.query.times[1]),
            *batch.states[1:])))]
    for fault in faults:
        with pytest.raises(KernelError):fault()
        assert run()==converted  # failures do not poison a subsequent valid call


def test_barycentric_space_time_scaling_commutes_with_linear_motion():
    # Independent analytic construction: scaling time and position leaves the
    # coordinate derivative unchanged; no second propagation belongs here.
    from decimal import Decimal,localcontext
    from wenu.astrometric_coordinates import TcbTdbAdapter
    from wenu_kernel.records import TimeSpan
    batch,a,receipts,converted=_converted_mixed_batch()
    epoch=TimePoint(2451545,0,'tcb')
    epoch_tdb=TcbTdbAdapter(a.coverage).convert(epoch,'tdb')
    with localcontext() as ctx:
        ctx.prec=90
        f=1-Decimal('1.550519768e-8')
        for s in converted.states:
            # Exact convention relations, independently evaluated using Decimal.
            dt=(Decimal(s.original.time.jd1-epoch.jd1)+Decimal(s.original.time.jd2))*86400
            expected=tuple(float(Decimal(p)*f+Decimal(v)*dt*f)
                for p,v in zip((1e12,0,0),(1000,2000,0)))
            assert s.position_m==expected
            actual_dt=(Decimal(s.time.jd1-epoch_tdb.target.jd1)+Decimal(s.time.jd2)
                       -Decimal(epoch_tdb.target.jd2))*86400
            assert abs(actual_dt-dt*f) <= Decimal(s.conversion.numerical_error_s)+Decimal(epoch_tdb.numerical_error_s)


@pytest.mark.parametrize('years',[-50000,-10000,-1,0,1,10000,50000])
def test_angular_shared_core_matches_independent_decimal_affine_oracle(years):
    """Protect reduced-model math across long domains; closest mixed-engine oracle."""
    from decimal import Decimal,localcontext
    from wenu.astrometric_state import AngularMotionRow
    from wenu_kernel.records import TimeSpan
    p=mixed_provider(RectilinearAstrometricProvider,AngularMotionRow,angular=True)
    a=p.describe().admissions[0]
    from math import floor
    days=365.25*years;whole=floor(days+.5)
    time=TimePoint(2451545+whole,days-whole,'tcb')
    q=StateQuery(a.catalogue,a.model,tuple(reversed(a.objects)),(time,),a.reference,AccuracyRequest())
    with Kernel(references=(a.reference,))as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((a.catalogue,)))as session:batch=session.evaluate(q)
    with localcontext()as ctx:
        ctx.prec=90
        dt=Decimal(years)*Decimal('365.25')*86400
        xyz=(Decimal(1),Decimal(2e-12)*dt,Decimal(1e-12)*dt)
        norm=sum(v*v for v in xyz).sqrt()
        oracle=tuple(float(v/norm)for v in xyz)
    for s in batch.states:
        assert max(abs(x-y)for x,y in zip(s.vector,oracle)) < 2**-48
        assert s.source_epoch==TimePoint(2451545,0,'tcb')
        assert s.evidence.physical_model.status=='not_evaluated'
    assert [s.object_key for s in batch.states]==list(reversed(a.objects))
    assert not hasattr(batch.states[0],'position_m')


@pytest.mark.parametrize('fault',['epoch','unit','radial','nonfinite','missing','unavailable_vectors','cartesian'])
def test_angular_rows_and_cartesian_masquerade_refuse(fault):
    from wenu.astrometric_state import AngularMotionRow
    args=['angular',TimePoint(2451545,0,'tcb'),(1.,0.,0.),(0.,1e-12,0.),None]
    if fault=='epoch':args[1]=None
    if fault=='unit':args[2]=(2.,0.,0.)
    if fault=='radial':args[3]=(1e-12,1e-12,0.)
    if fault=='nonfinite':args[3]=(0.,float('nan'),0.)
    if fault=='missing':args[3]=None
    if fault=='unavailable_vectors':args[4]='missing PM'
    with pytest.raises(ValueError):
        if fault=='cartesian':mixed_provider(RectilinearAstrometricProvider,AngularMotionRow,'cartesian',angular=True)
        else:AngularMotionRow(*args)


def test_angular_shared_core_numerical_fault_reuse_and_immutable_coefficients(monkeypatch):
    import wenu.astrometric_state as core
    from dataclasses import FrozenInstanceError
    p=mixed_provider(RectilinearAstrometricProvider,core.AngularMotionRow,angular=True)
    a=p.describe().admissions[0]
    row=p._lookup[a.objects[0]]
    assert type(row) is core.AngularMotionRow and not hasattr(row,'position_m')
    with pytest.raises(FrozenInstanceError):row.tangent_per_s=(0,0,0)
    q=StateQuery(a.catalogue,a.model,(a.objects[0],),(TimePoint(2451545,0,'tcb'),),a.reference,
                 AccuracyRequest(angular_rad=1e-5),evaluation_policy='bounded_reuse')
    calls=[];evaluate=p.evaluate
    def counted(q):calls.append(q);return evaluate(q)
    p.evaluate=counted
    with Kernel(references=(a.reference,))as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((a.catalogue,),reproducibility='interactive_bounded'))as session:
            first=session.evaluate(q)
            second=session.evaluate(replace(q,times=(TimePoint(2451545,.01,'tcb'),)))
            assert len(calls)==1 and second.states[0].anchor_time==first.states[0].anchor_time
            assert second.reuse_certificates
    # The exact affine-oracle check must detect a deliberate computed-vector fault.
    p=mixed_provider(RectilinearAstrometricProvider,core.AngularMotionRow,angular=True)
    a=p.describe().admissions[0]
    q=StateQuery(a.catalogue,a.model,(a.objects[0],),(TimePoint(2451545,.1,'tcb'),),a.reference,AccuracyRequest())
    baseline=p.evaluate(q)
    original=core._exact_position
    monkeypatch.setattr(core,'_exact_position',lambda r,t:(1,1,0))
    from wenu_kernel.errors import AccuracyUnavailable
    with pytest.raises(AccuracyUnavailable):p.evaluate(q)
    monkeypatch.setattr(core,'_exact_position',original)
    assert p.evaluate(q)==baseline
    p.close()


# Historical calendar boundary extends the existing time-convention/oracle owner.
def historical_date(**changes):
    from wenu.astrometric_coordinates import HistoricalDate
    return HistoricalDate(**dict(dict(year=2000, month=1, day=1, hour=12,
        calendar='gregorian', year_numbering='astronomical', scale='tcb',
        uncertainty_s=None), **changes))


def resolve_date(**changes):
    from wenu.astrometric_coordinates import resolve_historical_date
    from wenu_kernel.time import TimeService
    return resolve_historical_date(historical_date(**changes),time_service=TimeService())


@pytest.mark.parametrize('calendar,year,month,day,hour,jd', [
    ('gregorian',2000,1,1,12,2451545),
    ('julian',-4712,1,1,12,0),
    ('gregorian',-4713,11,24,12,0),
    ('julian',1582,10,4,0,2299159.5),
    ('gregorian',1582,10,15,0,2299160.5),
])
def test_historical_published_calendar_vectors(calendar,year,month,day,hour,jd):
    # USNO Julian Date converter/reform examples and SOFA J2000; these
    # check labels/JD arithmetic, not a UT1-to-TCB physical conversion.
    r=resolve_date(calendar=calendar,year=year,month=month,day=day,hour=hour)
    assert r.time.jd1+r.time.jd2==jd and r.calendar_rounding_error_s==0
    assert r.conversion.source is r.calendar_time
    assert r.conversion.target is r.calendar_time
    assert r.conversion.numerical_error_s==0


@pytest.mark.parametrize('year',[-4799,-4000,-1000,-400,-100,-4,-1,0,1,4,100,400,1582,1900,2000,50000])
def test_historical_gregorian_independent_erfa_calendar(year):
    import erfa
    from math import fsum
    r=resolve_date(year=year,month=3,day=1,hour=0)
    a,b=erfa.cal2jd(year,3,1)
    assert fsum((r.time.jd1-a,r.time.jd2,-b))==0


@pytest.mark.parametrize('calendar,cycle,days',[('gregorian',400,146097),('julian',4,1461)])
def test_historical_ancient_negative_year_cycles(calendar,cycle,days):
    # Exact leap-cycle identity independently exercises floor division before
    # the shifted algorithm origin; ERFA's calendar API rejects these years.
    for y in (-100000,-50000,-10000,-4801,-4800,-1,0,1,2000):
        a=resolve_date(calendar=calendar,year=y,month=3,day=1)
        b=resolve_date(calendar=calendar,year=y+cycle,month=3,day=1)
        assert b.time.jd1-a.time.jd1==days and a.time.jd2==b.time.jd2


def test_historical_bce_ce_year_zero_and_original_labels_are_preserved():
    from dataclasses import FrozenInstanceError
    for n in (1,2,400,1000,50000):
        bce=resolve_date(year=n,year_numbering='bce',uncertainty_s=86400.)
        astro=resolve_date(year=1-n)
        assert bce.time==astro.time
        assert bce.source.year==n and bce.source.year_numbering=='bce'
        assert bce.source.uncertainty_s==86400. and astro.source.uncertainty_s is None
    assert resolve_date(year=1,year_numbering='ce').time==resolve_date(year=1).time
    with pytest.raises(FrozenInstanceError): bce.source.year=1
    with pytest.raises(FrozenInstanceError): bce.calendar_time=bce.time


def test_historical_proleptic_calendars_do_not_silently_switch_at_reform():
    # Gregorian Oct 5 exists under the explicit proleptic policy. The same
    # labels in different calendars are different instants, not auto-corrected.
    a=resolve_date(year=1582,month=10,day=4)
    b=resolve_date(year=1582,month=10,day=5)
    c=resolve_date(calendar='julian',year=1582,month=10,day=5)
    assert b.time.jd1-a.time.jd1==1 and c.time.jd1-b.time.jd1==10
    resolve_date(calendar='julian',year=1900,month=2,day=29)
    from wenu_kernel.errors import InvalidQuery
    with pytest.raises(InvalidQuery): resolve_date(year=1900,month=2,day=29)
    resolve_date(year=0,month=2,day=29)


def test_historical_fractional_second_uses_two_parts_and_outward_decimal_bound():
    from decimal import Decimal,localcontext
    from math import nextafter
    with localcontext() as ctx:
        ctx.prec=100
        for second in (0.,1e-10,.1,59.99,nextafter(60.,0)):
            r=resolve_date(year=-50000,hour=23,minute=59,second=second)
            base=resolve_date(year=-50000,hour=0)
            # Compare in seconds: no rounded nonterminating Decimal /86400
            # can perturb an exactly representable outward bound.
            expected=Decimal(23*3600+59*60)+Decimal.from_float(second)
            actual=(Decimal(r.time.jd1-base.time.jd1)+Decimal.from_float(r.time.jd2)
                    -Decimal.from_float(base.time.jd2))*Decimal(86400)
            assert abs(actual-expected)<=Decimal.from_float(r.calendar_rounding_error_s)
        a=resolve_date(year=-50000,second=0)
        b=resolve_date(year=-50000,second=1e-10)
        assert a.time!=b.time and a.time.jd1+a.time.jd2==b.time.jd1+b.time.jd2


@pytest.mark.parametrize('changes',[
    {'year':True},{'year':1.0},{'month':0},{'month':13},{'day':0},{'day':32},
    {'year':1,'month':2,'day':29},{'hour':24},{'minute':60},{'second':60},
    {'second':True},{'second':float('nan')},{'second':-1},{'second':10**400},
    {'uncertainty_s':-1},{'uncertainty_s':True},{'uncertainty_s':float('inf')},
    {'uncertainty_s':'unknown'},{'calendar':'auto'},{'calendar':[]},
    {'year_numbering':'BC'},{'year_numbering':'bce','year':0},
    {'year_numbering':'ce','year':-1},{'scale':'utc'},{'scale':'ut1'},{'scale':None},
])
def test_historical_ambiguous_or_invalid_input_is_refused(changes):
    from wenu_kernel.errors import InvalidQuery
    resolve_date()  # success must not warm a fallback/default path
    with pytest.raises(InvalidQuery): historical_date(**changes)


def test_historical_requires_uncertainty_and_typed_explicit_service():
    from wenu.astrometric_coordinates import HistoricalDate,resolve_historical_date
    from wenu_kernel.errors import InvalidQuery
    from wenu_kernel.time import TimeService
    with pytest.raises(TypeError):
        HistoricalDate(year=1,month=1,day=1,calendar='julian',year_numbering='ce',scale='tcb')
    for date,service in (({},TimeService()),(historical_date(),None)):
        with pytest.raises(InvalidQuery): resolve_historical_date(date,time_service=service)
    with pytest.raises(InvalidQuery): resolve_date(year=10**15)
    zero=resolve_date(uncertainty_s=0)
    unknown=resolve_date(uncertainty_s=None)
    assert zero.time==unknown.time and zero.source!=unknown.source
    large=resolve_date(uncertainty_s=2**53+1)
    assert large.source.uncertainty_s==2**53+1  # do not round a source bound down


def test_historical_tdb_to_tcb_uses_admitted_receipt_not_scale_relabel():
    from wenu.astrometric_coordinates import TcbTdbAdapter,resolve_historical_date
    from wenu_kernel.records import TimeSpan
    from wenu_kernel.time import TimeService
    from wenu_kernel.errors import TimeConversionUnavailable,OutsideCoverage,AccuracyUnavailable
    date=historical_date(year=1000,year_numbering='bce',calendar='julian',scale='tdb',uncertainty_s=43200)
    adapter=TcbTdbAdapter(TimeSpan(TimePoint(1000000,0,'tdb'),TimePoint(3000000,0,'tdb')))
    service=TimeService((adapter,),admissions=(adapter.describe(),))
    r=resolve_historical_date(date,time_service=service)
    assert r.source is date and r.source.uncertainty_s==43200 and r.calendar_time.scale=='tdb'
    assert r.time.scale=='tcb' and r.time.jd2!=r.calendar_time.jd2
    assert r.conversion==service.convert(r.calendar_time,'tcb')
    assert r.conversion==_assert_barycentric_time_reference(adapter,r.calendar_time)
    with pytest.raises(AccuracyUnavailable): resolve_historical_date(date,time_service=service,maximum_conversion_error_s=0)
    for scale in ('tai','tt','tdb'):
        with pytest.raises(TimeConversionUnavailable):
            resolve_historical_date(replace(date,scale=scale),time_service=TimeService())
    with pytest.raises(OutsideCoverage): resolve_historical_date(replace(date,year=50000),time_service=service)
    assert resolve_historical_date(date,time_service=service)==r


# K4b.04: existing convention-owner tests protect frame bias, handedness,
# independent axes/date semantics and refusal without changing native states.
def tt_year(year):
    from fractions import Fraction
    value=Fraction(2451545)+(Fraction(str(year))-2000)*Fraction(1461,4)
    whole=(value+Fraction(1,2)).__floor__()
    return TimePoint(whole,float(value-whole),'tt')


def long_frame(year=2000, axes='mean-equator-equinox', **changes):
    from wenu.astrometric_coordinates import LongTermFrame
    from wenu_kernel.records import TimeSpan
    return LongTermFrame(**dict(dict(equinox=tt_year(year),
        validity=TimeSpan(tt_year(-198000),tt_year(202000)),axes=axes,
        model_policy='vcw2011-2012-erfa'),**changes))


@pytest.mark.parametrize('axes,year,reference',[
    ('mean-equator-equinox',1666.666,(
        (.9967044167723271851,.07437794731203340345,.03237632684841625547),
        (-.07437795663437177152,.9972293947500013666,-.001205741865911243235),
        (-.03237630543224664992,-.001206316791076485295,.9994750220222438819))),
    ('mean-ecliptic-equinox',-3000,(
        (.3564105644859788825,.8530575738617682284,.3811355207795060435),
        (-.9343283469640709942,.3247830597681745976,.1467872751535940865),
        (.001431636191201167793,-.4084222566960599342,.9127919865189030899))),
])
def test_long_frame_published_erfa_regression_matrix(axes,year,reference):
    # Published t_erfa_c.c t_ltpb / t_ltecm numerical reference vectors.
    # Conformity to the reference library, not an independent dynamics oracle.
    import numpy as np
    frame=long_frame(year,axes)
    np.testing.assert_allclose(frame.matrix,reference,rtol=0,atol=1e-14)
    assert frame.backend_jyear_tt==float(year)
    assert frame.physical_error_rad is frame.numerical_error_rad is None


@pytest.mark.parametrize('axes',['mean-equator-equinox','mean-ecliptic-equinox'])
@pytest.mark.parametrize('year',[-198000,-50000,-10000,-1000,0,2000,10000,50000,202000])
def test_long_frame_independent_pole_triad_and_matrix_application(axes,year):
    import erfa,numpy as np
    from decimal import Decimal,localcontext
    f=long_frame(year,axes)
    # Reconstruct axes geometrically from independently exposed pole functions;
    # these share model coefficients, so this is independent geometry only.
    pole=erfa.ltpequ(float(year));ecliptic=erfa.ltpecl(float(year))
    x=np.cross(pole,ecliptic);x/=np.linalg.norm(x)
    z=pole if axes=='mean-equator-equinox' else ecliptic
    y=np.cross(z,x)
    triad=np.array((x,y,z))
    # Isolate bias from the two independently exposed J2000 matrices: the
    # fitted long-term J2000 precession itself has tiny nonzero residuals.
    # Do not conflate the fitted residual with the ICRS frame bias.
    bias=np.linalg.solve(erfa.ltp(2000.),erfa.ltpb(2000.))
    np.testing.assert_allclose(f.matrix,triad@bias,rtol=0,atol=2e-14)
    np.testing.assert_allclose(np.array(f.matrix)@np.array(f.matrix).T,np.eye(3),rtol=0,atol=3e-14)
    assert np.linalg.det(f.matrix)>0
    v=(.36,.48,.8)
    with localcontext() as c:
        c.prec=80
        r=[sum(Decimal(a)*Decimal(b)for a,b in zip(row,v))for row in f.matrix]
        norm=sum(a*a for a in r).sqrt();oracle=tuple(float(a/norm)for a in r)
    np.testing.assert_allclose(f.rotate(v),oracle,rtol=0,atol=3e-16)
    back=np.linalg.solve(np.array(f.matrix),f.rotate(v));back/=np.linalg.norm(back)
    np.testing.assert_allclose(back,v,rtol=0,atol=5e-16)
    np.testing.assert_allclose(f.rotate(f.pole_icrs),(0,0,1),rtol=0,atol=2e-14)


@pytest.mark.parametrize('axes',['mean-equator-equinox','mean-ecliptic-equinox'])
def test_long_frame_near_modern_iau2006_agreement_without_switch(axes):
    import erfa,numpy as np
    from math import sqrt
    for year in range(1900,2101,10):
        f=long_frame(year,axes);t=tt_year(year)
        r=(erfa.pmat06 if axes=='mean-equator-equinox' else erfa.ecm06)(t.jd1,t.jd2)
        # Direct ERFA comparison is <1 mas here, not uniformly <100 uas.
        # This diagnostic threshold is not a physical error guarantee.
        assert np.linalg.norm(np.array(f.matrix)-r)/sqrt(2)<4.84813681109536e-9
        assert f.model.model_id=='wenu.astrometry:long-term-frame'
    assert abs(long_frame().matrix[0][1])>1e-8  # ICRS != mean J2000


def test_long_frame_binding_is_immutable_and_separates_exact_epoch_domain_and_backend():
    from dataclasses import FrozenInstanceError
    from wenu_kernel.records import TimeSpan
    a=long_frame();b=long_frame(equinox=replace(a.equinox,jd2=1e-12))
    assert a.matrix==b.matrix and a.model!=b.model  # backend rounds year; identity must not
    assert b.epoch_rounding_s>0 and a.epoch_rounding_s==0
    assert a.model!=long_frame(validity=TimeSpan(tt_year(1900),tt_year(2100))).model
    assert a.model!=long_frame(axes='mean-ecliptic-equinox').model
    with pytest.raises(FrozenInstanceError):a.equinox=tt_year(2001)
    with pytest.raises(TypeError):a.matrix[0][0]=0
    assert all(a.backend_versions) and a.equinox.scale=='tt'


@pytest.mark.parametrize('changes',[
    {'equinox':TimePoint(2451545,0,'tcb')}, {'equinox':None},
    {'equinox':tt_year(-198001)},{'equinox':tt_year(202001)},
    {'equinox':replace(tt_year(-198000),jd2=-1e-12)},
    {'equinox':replace(tt_year(202000),jd2=1e-12)},
    {'validity':None},{'axes':'fk5'},{'axes':'cirs'},{'model_policy':'auto'},
    {'maximum_physical_error_rad':0},{'maximum_physical_error_rad':1},
    {'maximum_physical_error_rad':-1},{'maximum_physical_error_rad':True},
    {'maximum_physical_error_rad':float('nan')},
    {'maximum_physical_error_rad':10**400},
])
def test_long_frame_invalid_implicit_or_accuracy_request_refuses_after_success(changes):
    from wenu_kernel.errors import KernelError
    good=long_frame();good.rotate((1.,0.,0.))
    with pytest.raises(KernelError):long_frame(**changes)
    assert long_frame()==good


@pytest.mark.parametrize('bad',[(0,0,0),(1,1,1),(float('nan'),0,1),(True,0,0),[1,0],None])
def test_long_frame_refuses_non_direction_input(bad):
    from wenu_kernel.errors import InvalidQuery
    with pytest.raises(InvalidQuery):long_frame().rotate(bad)


@pytest.mark.parametrize('bad',[[[1,0,0],[0,1,0],[0,0,-1]],[[2,0,0],[0,1,0],[0,0,1]],
    [[float('nan'),0,0],[0,1,0],[0,0,1]],[[1,0],[0,1]]])
def test_long_frame_malformed_backend_never_publishes_orientation(monkeypatch,bad):
    import erfa
    from wenu_kernel.errors import InvalidProviderResult
    good=long_frame();monkeypatch.setattr(erfa,'ltpb',lambda ep:bad)
    with pytest.raises(InvalidProviderResult):long_frame()
    assert good.rotate((1.,0.,0.))  # admitted immutable matrix never consults warm backend


def test_long_frame_dropped_bias_fault_breaks_reference_and_backend_cause_is_preserved(monkeypatch):
    import erfa,numpy as np
    from wenu_kernel.errors import ProviderEvaluationError
    baseline=long_frame();monkeypatch.setattr(erfa,'ltpb',erfa.ltp)
    with pytest.raises(AssertionError):
        np.testing.assert_allclose(long_frame().matrix,baseline.matrix,rtol=0,atol=1e-14)
    def fail(ep):raise RuntimeError('injected backend fault')
    monkeypatch.setattr(erfa,'ltpb',fail)
    with pytest.raises(ProviderEvaluationError)as caught:long_frame()
    assert isinstance(caught.value.__cause__,RuntimeError)


def test_long_frame_native_batch_view_preserves_sdk_states_and_refuses_foreign_binding():
    from wenu.astrometric_state import AngularMotionRow
    from wenu.astrometric_coordinates import orient_direction_batch
    from wenu_kernel.errors import KernelError
    p=mixed_provider(RectilinearAstrometricProvider,AngularMotionRow,angular=True)
    a=p.describe().admissions[0];q=StateQuery(a.catalogue,a.model,a.objects,
        (TimePoint(0,0,'tcb'),),a.reference,AccuracyRequest())
    with Kernel(references=(a.reference,))as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((a.catalogue,)))as session:batch=session.evaluate(q)
    frame=long_frame(-10000);out=orient_direction_batch(batch,admission=a,orientation=frame)
    assert out.original is batch and out.orientation is frame
    for native,derived in zip(batch.states,out.states):
        assert derived.original is native
        assert derived.vector==frame.rotate(native.vector)
        assert native.time.scale=='tcb' and frame.equinox.scale=='tt'
        assert native.evidence.physical_model.status=='not_evaluated'
    bad=[dict(admission=replace(a,model=replace(a.model,version='foreign'))),dict(orientation=None)]
    for changes in bad:
        with pytest.raises(KernelError):orient_direction_batch(batch,**dict(dict(admission=a,orientation=frame),**changes))
    with pytest.raises(KernelError):orient_direction_batch(replace(batch,states=batch.states[::-1]),admission=a,orientation=frame)
    assert orient_direction_batch(batch,admission=a,orientation=frame)==out


def test_long_frame_finite_domain_and_partial_warm_batches_refuse():
    from wenu.astrometric_state import AngularMotionRow
    from wenu.astrometric_coordinates import orient_direction_batch
    from wenu_kernel.records import TimeSpan,UnboundedCoverage
    from wenu_kernel.errors import KernelError
    for validity in (UnboundedCoverage('tt'),TimeSpan(TimePoint(0,0,'tcb'),TimePoint(3000000,0,'tcb')),
                     TimeSpan(tt_year(2001),tt_year(2100)),TimeSpan(tt_year(-198001),tt_year(2001))):
        with pytest.raises(KernelError):long_frame(validity=validity)
    p=mixed_provider(RectilinearAstrometricProvider,AngularMotionRow,angular=True)
    a=p.describe().admissions[0];q=StateQuery(a.catalogue,a.model,a.objects,
        (TimePoint(2451545,0,'tcb'),),a.reference,AccuracyRequest())
    with Kernel(references=(a.reference,))as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((a.catalogue,)))as session:batch=session.evaluate(q)
    frame=long_frame();baseline=orient_direction_batch(batch,admission=a,orientation=frame)
    bad=(replace(batch,states=batch.states[:-1]),
         replace(batch,states=(replace(batch.states[0],time=TimePoint(2451546,0,'tcb')),)+batch.states[1:]),
         replace(batch,states=(replace(batch.states[0],source_epoch=None),)+batch.states[1:]),
         replace(batch,query=replace(q,require_velocity=True)))
    for value in bad:
        with pytest.raises(KernelError):orient_direction_batch(value,admission=a,orientation=frame)
    assert orient_direction_batch(batch,admission=a,orientation=frame)==baseline

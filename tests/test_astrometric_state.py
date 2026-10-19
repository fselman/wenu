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


def mixed_provider(provider_class, row_class, representation="direction", scale="tcb"):
    """Constructed inputs for four families, with no catalogue-specific fixture."""
    from wenu_kernel.records import (
        CatalogueRef, CatalogueSnapshot, ExternalId, ModelAdmission, ModelRef,
        ObjectKey, ObjectRecord, ProviderDescriptor, ProviderKey, ReferenceSpec,
        ResourceRef, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
    )
    epoch = TimePoint(2451545, 0, scale)
    span = TimeSpan(TimePoint(2451544, 0, scale), TimePoint(2451546, 0, scale))
    cartesian = representation == 'cartesian'
    key = ProviderKey('constructed-mixed-astrometry'+('.pv' if cartesian else ''), '1')
    resource = ResourceRef('constructed-si-solutions', '1', 'a'*64, span,
                           'synthetic nominal domain', ('Constructed test inputs',))
    kinds = ('star', 'open-cluster', 'planetary-nebula', 'supernova-remnant')
    keys = tuple(ObjectKey('constructed:'+kind) for kind in kinds)
    ref = CatalogueRef(key, (resource,), 'b'*64)
    model = ModelRef('constructed-rectilinear', '1', 'c'*64, (resource,))
    frame = ReferenceSpec('icrs','solar-system-barycenter','nominal-astrometric',
                          representation,'m,m/s' if cartesian else 'rad','synthetic no additional light time')
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
    rows = [(k,row_class(kind,epoch,(1e12,0.,0.),(1000.,2000.,0.),None))
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

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


def mixed_provider(provider_class, row_class, representation="direction"):
    """Constructed inputs for four families, with no catalogue-specific fixture."""
    from wenu_kernel.records import (
        CatalogueRef, CatalogueSnapshot, ExternalId, ModelAdmission, ModelRef,
        ObjectKey, ObjectRecord, ProviderDescriptor, ProviderKey, ReferenceSpec,
        ResourceRef, TimePoint, TimeSpan, UncertaintyChannel, UncertaintyEvidence,
    )
    epoch = TimePoint(2451545, 0, 'tcb')
    span = TimeSpan(TimePoint(2451544, 0, 'tcb'), TimePoint(2451546, 0, 'tcb'))
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
    script = '''
import sys,importlib.util
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
        assert all(row.velocity_available for row in s.evaluate(q).states)
assert not any(n.split('.')[0] in ('wenu','astropy','numpy') for n in sys.modules)
'''
    result = subprocess.run([sys.executable,'-I','-S','-c',script,str(core),
        str(Path(wenu_kernel.__file__).resolve().parent.parent),inspect.getsource(mixed_provider)],
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

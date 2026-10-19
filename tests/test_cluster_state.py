"""Cluster solution admission, independent motion oracles and kernel isolation."""
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import json
from math import cos, sin, radians, fsum, sqrt

import numpy as np
import pytest
from astropy import units as u
from astropy.table import Table, MaskedColumn

from wenu.cluster_state import (ClusterMotionProvider, admit_cluster_motion,
                               load_cluster_motion, _canonical_digest)
from wenu_kernel import Kernel
from wenu_kernel.errors import KernelError, UnsupportedCapability, ClosedSession
from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery, TimePoint, TimeSpan

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'src/wenu/data/catalogs/open_clusters'


def synthetic():
    """Constructed motion cases; no frozen-provider or physical-accuracy claim."""
    table = Table(dict(wenu_id=['east', 'north-pole', 'south-pole', 'still'],
        centre_source=['constructed']*4, RAdeg=[359.999, 23., 178., 90.],
        DEdeg=[0., 90., -89.999999, 20.], dist50=[10., 100., 50., 5.],
        pmRA=[400., -100., 220., 0.], pmDE=[10., 80., -120., 0.], RV=[50., -20., 30., 0.]),
        meta=dict(selected_catalogue_sha256='0'*64, astrometry_source={'constructed': True}))
    for name, unit in [('RAdeg',u.deg),('DEdeg',u.deg),('dist50',u.pc),
                       ('pmRA',u.mas/u.yr),('pmDE',u.mas/u.yr),('RV',u.km/u.s)]:
        table[name].unit = unit
    meta = json.loads((DATA/'open_clusters_hunt_motion_admission_v1.json').read_text())
    meta.update(namespace='test-clusters',edition='synthetic-1',source_name='constructed',
                provenance='Constructed synthetic fixture', selected_catalogue_sha256='0'*64,
                source_spec_digest=_canonical_digest(table.meta['astrometry_source']))
    coverage = TimeSpan(TimePoint(2400000,0,'tcb'), TimePoint(2500000,0,'tcb'))
    return table, meta, coverage


def query_for(provider, times=None, objects=None):
    a = provider.describe().admissions[0]
    return StateQuery(a.catalogue,a.model,a.objects if objects is None else objects,
        times or (TimePoint(2457389,0,'tcb'),),a.reference,AccuracyRequest())


def through_kernel(provider, query):
    with Kernel(references=(query.reference,)) as kernel:
        kernel.register(provider, ownership='borrowed')
        with kernel.open_session(SessionPolicy(provider.describe().catalogues)) as session:
            return session.evaluate(query)


@pytest.mark.parametrize('days',[-3652500., -36525., -365.25, 0., 365.25, 36525., 3652500.])
def test_cluster_motion_matches_independent_erfa_pv_oracle_at_poles_and_wrap(days):
    # Protect conversion, cos(dec), RV sign, units and elapsed-time arithmetic.
    # Independent scalar trig constructs PV; ERFA performs the oracle update.
    import erfa
    table, meta, coverage = synthetic()
    coverage = TimeSpan(TimePoint(-2000000,0,'tcb'),TimePoint(7000000,0,'tcb'))
    provider = ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
    day = int(np.floor(days+.5)); fraction = days-day
    time = TimePoint(2457389+day, fraction,'tcb')
    result = through_kernel(provider,query_for(provider,(time,)))
    for source,state in zip(table,result.states):
        a,d = radians(source['RAdeg']),radians(source['DEdeg'])
        direction = np.array([cos(a)*cos(d),sin(a)*cos(d),sin(d)])
        east = np.array([-sin(a),cos(a),0.])
        north = np.array([-cos(a)*sin(d),-sin(a)*sin(d),cos(d)])
        distance = source['dist50']*u.pc.to(u.m)
        factor = u.mas.to(u.rad)/u.yr.to(u.s)
        pv = np.zeros((),dtype=erfa.dt_pv)
        pv['p'] = distance*direction
        pv['v'] = distance*factor*(source['pmRA']*east+source['pmDE']*north)+source['RV']*1000*direction
        expected = erfa.pvu(days*86400,pv)['p']
        expected /= np.linalg.norm(expected)
        np.testing.assert_allclose(state.vector,expected,rtol=0,atol=8e-16)
        assert state.time == state.anchor_time == time
        assert state.source_epoch == TimePoint(2457389,0,'tcb')
    if days > 3652.5:
        first = result.states[0].vector
        assert np.arctan2(first[1],first[0]) > 0  # crosses RA=0


def test_cluster_perspective_motion_matches_analytic_case_and_responds_to_rv():
    table,meta,coverage = synthetic()
    table['RAdeg'][0] = table['DEdeg'][0] = 0.
    table['pmDE'][0] = 0.
    elapsed = 36525*86400
    time = TimePoint(2457389+36525,0,'tcb')
    def angle(rv):
        table['RV'][0] = rv
        p = ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
        state = through_kernel(p,query_for(p,(time,))).states[0]
        return np.arctan2(state.vector[1],state.vector[0])
    for rv in (-50.,0.,50.):
        d = table['dist50'][0]*u.pc.to(u.m)
        mu = table['pmRA'][0]*u.mas.to(u.rad)/u.yr.to(u.s)
        expected = np.arctan2(d*mu*elapsed,d+rv*1000*elapsed)
        assert abs(angle(rv)-expected) < 1e-17
    assert angle(-50) > angle(0) > angle(50)


def test_cluster_admission_preserves_all_source_rows_masks_and_immutable_metadata():
    coverage=TimeSpan(TimePoint(2451545,0,'tcb'),TimePoint(2462503,-.5,'tcb'))
    admitted=load_cluster_motion(DATA/'open_clusters_hunt_astrometry_v1.ecsv',
        DATA/'open_clusters_hunt_motion_admission_v1.json',coverage=coverage)
    provider=ClusterMotionProvider(admitted)
    snapshot=provider.catalogue(provider.describe().catalogues[0])
    # Model changes must not create a second identity for the same Wenu objects.
    from wenu.objects.open_clusters import OpenClusters
    lookup_layer=OpenClusters(None)
    source=lookup_layer.load()
    lookup_metadata=lookup_layer.catalogue_metadata_for(source)
    source_rows=[(str(row['wenu_id']),float(row['ra_deg']),float(row['dec_deg'])) for row in source]
    lookup=lookup_layer._direction_provider(source_rows,lookup_metadata.source_epochs,lookup_metadata,'tcb')
    assert tuple(row.key for row in snapshot.objects)==lookup.describe().admissions[0].objects
    lookup.close()
    assert len(snapshot.objects)==len(admitted.rows)==513
    assert len(provider.describe().admissions[0].objects)==502
    unavailable=admitted.to_record()['unavailable']
    assert len(unavailable)==11
    assert sum(reason=='missing rv' for reason in unavailable.values())==7
    assert sum(reason=='unqualified centre epoch/source' for reason in unavailable.values())==4
    original=admitted.source_table()
    original['pmRA'][0]=999
    assert admitted.source_table()['pmRA'][0]!=999
    record=admitted.to_record();record['source_metadata']['astrometry']['epoch_scale']='tt'
    assert admitted.to_record()['source_metadata']['astrometry']['epoch_scale']=='tcb'
    with pytest.raises(FrozenInstanceError): admitted.rows[0].position_m=(0.,0.,0.)
    key=next(row.key for row in snapshot.objects if row.key.value.endswith(':WOC00001229'))
    q=query_for(provider,objects=(key,))
    assert not provider.supports(q).supported
    assert 'unqualified' in provider.supports(q).reason
    with pytest.raises(UnsupportedCapability): through_kernel(provider,q)


def test_cluster_metadata_controls_epoch_and_units_without_hidden_source_literals():
    table,meta,coverage=synthetic();meta['astrometry']['epoch_label']='J2030.0'
    admitted=admit_cluster_motion(table,meta,coverage=coverage)
    assert admitted.rows[0].source_epoch==TimePoint(2462503,-.5,'tcb')
    table['pmRA']=table['pmRA'].quantity.to(u.arcsec/u.yr)
    converted=admit_cluster_motion(table,meta,coverage=coverage)
    np.testing.assert_allclose(converted.rows[0].velocity_m_s,admitted.rows[0].velocity_m_s,rtol=1e-15)
    assert converted.rows[0].source_epoch==admitted.rows[0].source_epoch


@pytest.mark.parametrize('fault',['selection','source-facts','frame','scale','pm-convention','policy',
                                  'unit','unitless','nan','negative-distance','latitude','duplicate-id'])
def test_cluster_admission_refuses_invalid_source_before_publication(fault):
    table,meta,coverage=synthetic()
    if fault=='selection': meta['selected_catalogue_sha256']='1'*64
    if fault=='source-facts': meta['source_spec_digest']='1'*64
    if fault=='frame': meta['astrometry']['frame']='fk5'
    if fault=='scale': meta['astrometry']['epoch_scale']='tt'
    if fault=='pm-convention': meta['astrometry']['ra_motion_convention']='mu_alpha'
    if fault=='policy': meta['policies']['radial_velocity']='assume-zero'
    if fault=='unit': table['pmRA'].unit=u.deg
    if fault=='unitless': table['pmRA'].unit=None
    if fault=='nan': table['pmRA'][0]=np.nan
    if fault=='negative-distance': table['dist50'][0]=-1
    if fault=='latitude': table['DEdeg'][0]=91
    if fault=='duplicate-id': table['wenu_id'][0]=table['wenu_id'][1]
    with pytest.raises(ValueError): admit_cluster_motion(table,meta,coverage=coverage)


def test_cluster_motion_refuses_subfloor_accuracy_wrong_scale_domain_and_velocity():
    table,meta,coverage=synthetic();p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage));q=query_for(p)
    for invalid in (replace(q,accuracy=AccuracyRequest(angular_rad=1e-15)),
                    replace(q,times=(TimePoint(2457389,0,'tt'),)),
                    replace(q,times=(TimePoint(2500001,0,'tcb'),)),
                    replace(q,require_velocity=True)):
        assert not p.supports(invalid).supported
        with pytest.raises(KernelError): through_kernel(p,invalid)
    with pytest.raises(UnsupportedCapability): p.certify(q,through_kernel(p,q))
    p.close()
    with pytest.raises(ClosedSession): p.evaluate(q)


def test_cluster_motion_preserves_subday_time_and_explicit_missing_rv():
    table,meta,coverage=synthetic()
    table['RV']=MaskedColumn(table['RV'],mask=[True,False,False,False],unit=u.km/u.s)
    admitted=admit_cluster_motion(table,meta,coverage=coverage)
    assert admitted.rows[0].unavailable_reason=='missing rv' and admitted.rows[0].velocity_m_s is None
    p=ClusterMotionProvider(admitted);a=p.describe().admissions[0]
    times=(TimePoint(2457389,0,'tcb'),TimePoint(2457389,1e-6,'tcb'))
    batch=through_kernel(p,query_for(p,times))
    assert batch.states[0].vector!=batch.states[len(a.objects)].vector


def test_cluster_domain_refuses_origin_crossing_and_unbounded_admission():
    from wenu_kernel.records import UnboundedCoverage
    table,meta,coverage=synthetic()
    with pytest.raises(ValueError): admit_cluster_motion(table,meta,coverage=UnboundedCoverage('tcb'))
    table['pmRA'][0]=table['pmDE'][0]=0.
    table['RV'][0]=-1e8  # constructed pathological model domain, not a physical source
    with pytest.raises(ValueError,match='singular'): admit_cluster_motion(table,meta,coverage=coverage)


def test_cluster_motion_provider_passes_shipped_conformance():
    import io,unittest
    from wenu_kernel.conformance import ProviderCase,ProviderActivity,provider_suite
    def factory():
        table,meta,coverage=synthetic();p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
        q=query_for(p,(TimePoint(2457389,0,'tcb'),TimePoint(2457754,.25,'tcb')))
        probe=replace(q,times=(TimePoint(2458120,-.5,'tcb'),))
        counts=dict(evaluate=0,certify=0,close=0);evaluate,certify,close=p.evaluate,p.certify,p.close
        def measured(query): counts['evaluate']+=1;return evaluate(query)
        def certificate(query,anchor): counts['certify']+=1;return certify(query,anchor)
        def cleanup(): counts['close']+=1;return close()
        p.evaluate,p.certify,p.close=measured,certificate,cleanup
        def mutate(): table['RAdeg'][0]=123;meta['astrometry']['epoch_label']='J2000.0'
        return ProviderCase(p,q,probe,lambda:ProviderActivity(counts['evaluate'],counts['certify'],counts['close']),mutate,
            replace(q,evaluation_policy='bounded_reuse',accuracy=AccuracyRequest(angular_rad=1e-5)))
    result=unittest.TextTestRunner(stream=io.StringIO()).run(provider_suite(factory,name='ClusterMotionContract'))
    assert result.wasSuccessful(),result.errors+result.failures
    assert result.testsRun==8 and not result.skipped


def test_cluster_epoch_queries_do_not_evaluate_static_galaxy_or_stellar_providers():
    from wenu.catalogue_state import CatalogueDirectionProvider
    from wenu_kernel.records import ReferenceSpec,UnboundedCoverage
    table,meta,coverage=synthetic();cluster=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
    unrelated=[]
    for name,capability in [('galaxy','static_direction'),('star','native_direction')]:
        p=CatalogueDirectionProvider([('other',1.,2.)],namespace=name,source_epoch=TimePoint(2457389,0,'tcb'),
            provenance=('Constructed isolated provider',),catalogue_edition='fixture',
            reference=ReferenceSpec('icrs','solar-system-barycenter','fixture-'+name,'direction','rad','test only'),
            capability=capability,semantic_type=name,provider_id='test-'+name,resource_id=name,model_id=name,
            coverage=UnboundedCoverage('tcb'))
        def forbidden(query): pytest.fail('Unrelated provider was evaluated')
        p.evaluate=forbidden;unrelated.append(p)
    providers=[cluster,*unrelated];references=[p.describe().admissions[0].reference for p in providers]
    with Kernel(references=references) as kernel:
        for p in providers: kernel.register(p,ownership='borrowed')
        with kernel.open_session(SessionPolicy(tuple(p.describe().catalogues[0] for p in providers),
                reproducibility='interactive_bounded')) as session:
            q=replace(query_for(cluster),evaluation_policy='bounded_reuse',accuracy=AccuracyRequest(angular_rad=1e-7))
            first=session.evaluate(q)
            near=session.evaluate(replace(q,times=(TimePoint(2457389,.001,'tcb'),)))
            assert all(row.certificate_id for row in near.states)
            assert first.states[0].vector==near.states[0].vector
            later=session.evaluate(replace(q,times=(TimePoint(2457754,.25,'tcb'),)))
            assert first.states[0].vector!=later.states[0].vector


def test_cluster_loader_refuses_changed_companion_bytes(tmp_path):
    source=tmp_path/'changed.ecsv';source.write_bytes((DATA/'open_clusters_hunt_astrometry_v1.ecsv').read_bytes()+b'\n')
    with pytest.raises(ValueError,match='do not match'):
        load_cluster_motion(source,DATA/'open_clusters_hunt_motion_admission_v1.json',
            coverage=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb')))



def reuse_query(provider, *, objects=None, tolerance=1e-5):
    return replace(query_for(provider, objects=objects), evaluation_policy='bounded_reuse',
                   accuracy=AccuracyRequest(angular_rad=tolerance))


def angular_distance(first, second):
    return np.arctan2(np.linalg.norm(np.cross(first,second)),np.dot(first,second))


def decimal_direction(row,time):
    # Independent high-precision arithmetic on the admitted mathematical model.
    # Does not call production rational/cone/time helpers or normalization.
    from decimal import Decimal, localcontext
    with localcontext() as ctx:
        ctx.prec=80
        elapsed=(Decimal(time.jd1-row.source_epoch.jd1)+Decimal(time.jd2)
                 -Decimal(row.source_epoch.jd2))*Decimal(86400)
        p=[Decimal(x)+elapsed*Decimal(v) for x,v in zip(row.position_m,row.velocity_m_s)]
        norm=sum(x*x for x in p).sqrt()
        return tuple(float(x/norm) for x in p)


@pytest.mark.parametrize('index',[0,1,2,3])
def test_cluster_certificate_bounds_entire_interval_and_anchor_numerical_error(index):
    from wenu_kernel.reuse import validate_certificate
    table,meta,coverage=synthetic()
    # Close, fast perspective case: endpoint-only drift estimates would be unsafe.
    table['RV'][0]=-1000.; table['dist50'][0]=.3
    admitted=admit_cluster_motion(table,meta,coverage=coverage);p=ClusterMotionProvider(admitted)
    key=p.describe().admissions[0].objects[index]
    q=reuse_query(p,objects=(key,),tolerance=1e-6)
    full=replace(q,evaluation_policy='full_model')
    anchor=through_kernel(p,full);cert=p.certify(q,anchor)
    validate_certificate(cert,anchor,p.describe().admissions[0])
    assert cert.maximum_error<=q.accuracy.angular_rad
    assert cert.maximum_error>=anchor.states[0].evidence.numerical.value>0
    assert cert.validity.contains(anchor.states[0].anchor_time)
    assert coverage.contains(cert.validity.start) and coverage.contains(cert.validity.stop)
    # Decimal reference and explicit interval endpoints; samples supplement the
    # analytical convex-cone proof, not a sampled speed bound.
    start,stop=cert.validity.start,cert.validity.stop
    for f in np.linspace(0.,1.,41):
        delta=(stop.jd1-start.jd1)+(stop.jd2-start.jd2)
        value=start.jd2+f*delta;whole=int(np.floor(value+.5))
        time=TimePoint(start.jd1+whole,float(value-whole),'tcb')
        expected=decimal_direction(admitted.rows[index],time)
        assert angular_distance(anchor.states[0].vector,expected)<=cert.maximum_error
    if index==3: assert cert.validity==coverage  # Explicitly zero velocity, not missing data.
    assert anchor.states[0].evidence.measurement.status=='not_evaluated'
    assert anchor.states[0].evidence.physical_model.status=='not_evaluated'


def test_cluster_reuse_skips_only_eligible_objects_and_keeps_original_anchor():
    table,meta,coverage=synthetic();p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
    a=p.describe().admissions[0];q=reuse_query(p,objects=(a.objects[0],a.objects[3]),tolerance=1e-6)
    rows=[];evaluate=p.evaluate
    def counted(query): rows.extend((t,k) for t in query.times for k in query.objects);return evaluate(query)
    p.evaluate=counted
    with Kernel(references=(q.reference,)) as kernel:
        kernel.register(p,ownership='borrowed')
        with kernel.open_session(SessionPolicy((q.catalogue,),reproducibility='interactive_bounded')) as session:
            first=session.evaluate(q);assert len(rows)==2
            near=TimePoint(2457389,.01,'tcb');later=session.evaluate(replace(q,times=(near,)))
            assert len(rows)==2
            assert all(x.anchor_time==q.times[0] and x.time==near and x.certificate_id for x in later.states)
            assert tuple(x.vector for x in first.states)==tuple(x.vector for x in later.states)
            # Every further reuse retains the original anchor, never a chain.
            second=TimePoint(2457389,.02,'tcb');again=session.evaluate(replace(q,times=(second,)))
            assert len(rows)==2 and all(x.anchor_time==q.times[0] for x in again.states)
            far=TimePoint(2457389+1000,0,'tcb');outside=session.evaluate(replace(q,times=(far,)))
            assert len(rows)==3 and rows[-1]==(far,a.objects[0])
            assert outside.states[0].anchor_time==far
            assert outside.states[1].anchor_time==q.times[0]
            # A looser old certificate cannot satisfy a tighter request.
            strict=replace(q,times=(near,),accuracy=AccuracyRequest(angular_rad=1e-9))
            session.evaluate(strict);assert len(rows)==5


def test_cluster_reproducible_mode_uses_full_model_and_is_order_independent():
    table,meta,coverage=synthetic()
    def run(order):
        p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage));q=reuse_query(p)
        with Kernel(references=(q.reference,)) as kernel:
            kernel.register(p,ownership='borrowed')
            with kernel.open_session(SessionPolicy((q.catalogue,))) as session:
                output={}
                for t in order: output[t]=session.evaluate(replace(q,times=(t,)))
                return output
    times=(TimePoint(2457389,0,'tcb'),TimePoint(2457389,.01,'tcb'))
    first=run(times);assert first==run(tuple(reversed(times)))
    assert all(row.anchor_time==row.time and row.certificate_id is None for result in first.values() for row in result.states)


def test_cluster_certificate_boundary_coverage_refusal_and_foreign_or_reused_anchor():
    table,meta,coverage=synthetic();p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
    a=p.describe().admissions[0];q=reuse_query(p,objects=(a.objects[0],),tolerance=1e-6)
    anchor=through_kernel(p,replace(q,evaluation_policy='full_model'));cert=p.certify(q,anchor)
    with Kernel(references=(q.reference,)) as kernel:
        kernel.register(p,ownership='borrowed')
        with kernel.open_session(SessionPolicy((q.catalogue,),reproducibility='interactive_bounded')) as session:
            session.evaluate(q)
            edge=session.evaluate(replace(q,times=(cert.validity.stop,),coverage=cert.validity))
            assert edge.states[0].anchor_time==q.times[0] and edge.states[0].certificate_id
            assert edge.reuse_certificates[0].maximum_error<=q.accuracy.angular_rad
            with pytest.raises(KernelError): p.certify(replace(q,times=(cert.validity.stop,)),edge)
            with pytest.raises(KernelError): session.evaluate(replace(q,coverage=coverage))
    foreign=replace(q,reference=replace(q.reference,status='foreign'))
    with pytest.raises(KernelError): p.certify(foreign,anchor)
    malformed=replace(anchor,states=(replace(anchor.states[0],vector=(0.,1.,0.)),))
    with pytest.raises(KernelError): p.certify(q,malformed)
    # Immediately outside a certified endpoint must not retain that anchor.
    outside=replace(cert.validity.stop,jd2=float(np.nextafter(cert.validity.stop.jd2,.5)))
    from wenu_kernel.reuse import qualifies
    assert not qualifies(cert,q,outside)


def test_cluster_numerical_bound_refuses_corrupted_elapsed_time(monkeypatch):
    import wenu.astrometric_state as owner
    table,meta,coverage=synthetic();p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage))
    q=query_for(p,(TimePoint(2457754,.25,'tcb'),))
    through_kernel(p,q)  # Positive baseline before injecting an actual numerical fault.
    monkeypatch.setattr(owner,'_seconds',lambda time,epoch:0.)
    with pytest.raises(KernelError): through_kernel(p,q)


@pytest.mark.parametrize('days',[-3652500.,-36525.,0.,365.25,3652500.])
def test_cluster_cartesian_matches_independent_erfa_pv_and_retains_all_identities(days):
    import erfa
    table,meta,_=synthetic()
    coverage=TimeSpan(TimePoint(-2000000,0,'tcb'),TimePoint(7000000,0,'tcb'))
    catalogue=admit_cluster_motion(table,meta,coverage=coverage)
    p=ClusterMotionProvider(catalogue,representation='cartesian')
    direction=ClusterMotionProvider(catalogue)
    assert p.describe().catalogues[0].provider!=direction.describe().catalogues[0].provider
    assert p.describe().admissions[0].objects==direction.describe().admissions[0].objects
    day=int(np.floor(days+.5));time=TimePoint(2457389+day,days-day,'tcb')
    q=replace(query_for(p,(time,)),accuracy=AccuracyRequest(metric='euclidean_norm'),require_velocity=True)
    result=through_kernel(p,q)
    for source,state in zip(table,result.states):
        a,d=radians(source['RAdeg']),radians(source['DEdeg'])
        axis=np.array([cos(a)*cos(d),sin(a)*cos(d),sin(d)])
        east=np.array([-sin(a),cos(a),0.]);north=np.array([-cos(a)*sin(d),-sin(a)*sin(d),cos(d)])
        distance=source['dist50']*u.pc.to(u.m);factor=u.mas.to(u.rad)/u.yr.to(u.s)
        pv=np.zeros((),dtype=erfa.dt_pv);pv['p']=distance*axis
        pv['v']=distance*factor*(source['pmRA']*east+source['pmDE']*north)+source['RV']*1000*axis
        expected=erfa.pvu(days*86400,pv)
        np.testing.assert_allclose(state.position_m,expected['p'],rtol=2e-15,atol=1e3)
        np.testing.assert_allclose(state.velocity_m_s,expected['v'],rtol=2e-15,atol=1e-9)
        assert state.time==state.anchor_time==time
        assert state.position_evidence.measurement.status=='not_evaluated'
        assert state.velocity_evidence.numerical.units=='m/s'


def test_real_cluster_cartesian_keeps_unavailable_rows_and_rejects_mixed_selection():
    coverage=TimeSpan(TimePoint(2451545,0,'tcb'),TimePoint(2462503,-.5,'tcb'))
    catalogue=load_cluster_motion(DATA/'open_clusters_hunt_astrometry_v1.ecsv',
        DATA/'open_clusters_hunt_motion_admission_v1.json',coverage=coverage)
    p=ClusterMotionProvider(catalogue,representation='cartesian');a=p.describe().admissions[0]
    assert len(p.catalogue(a.catalogue).objects)==513 and len(a.objects)==502
    unavailable=next(row.key for row in p.catalogue(a.catalogue).objects if row.key not in a.objects)
    q=replace(query_for(p,objects=(a.objects[0],unavailable)),accuracy=AccuracyRequest(metric='euclidean_norm'))
    assert not p.supports(q).supported
    with pytest.raises(KernelError):through_kernel(p,q)
    with pytest.raises(ValueError):ClusterMotionProvider(catalogue,representation='unknown')

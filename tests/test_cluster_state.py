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


def test_cluster_motion_refuses_accuracy_wrong_scale_domain_velocity_and_reuse():
    table,meta,coverage=synthetic();p=ClusterMotionProvider(admit_cluster_motion(table,meta,coverage=coverage));q=query_for(p)
    for invalid in (replace(q,accuracy=AccuracyRequest(angular_rad=1e-5)),
                    replace(q,times=(TimePoint(2457389,0,'tt'),)),
                    replace(q,times=(TimePoint(2500001,0,'tcb'),)),
                    replace(q,require_velocity=True),
                    replace(q,evaluation_policy='bounded_reuse',accuracy=AccuracyRequest(angular_rad=1e-5))):
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
        counts=dict(evaluate=0,close=0);evaluate,close=p.evaluate,p.close
        def measured(query): counts['evaluate']+=1;return evaluate(query)
        def cleanup(): counts['close']+=1;return close()
        p.evaluate,p.close=measured,cleanup
        def mutate(): table['RAdeg'][0]=123;meta['astrometry']['epoch_label']='J2000.0'
        return ProviderCase(p,q,probe,lambda:ProviderActivity(counts['evaluate'],0,counts['close']),mutate)
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
        with kernel.open_session(SessionPolicy(tuple(p.describe().catalogues[0] for p in providers))) as session:
            first=session.evaluate(query_for(cluster))
            later=session.evaluate(query_for(cluster,(TimePoint(2457754,.25,'tcb'),)))
            assert first.states[0].vector!=later.states[0].vector


def test_cluster_loader_refuses_changed_companion_bytes(tmp_path):
    source=tmp_path/'changed.ecsv';source.write_bytes((DATA/'open_clusters_hunt_astrometry_v1.ecsv').read_bytes()+b'\n')
    with pytest.raises(ValueError,match='do not match'):
        load_cluster_motion(source,DATA/'open_clusters_hunt_motion_admission_v1.json',
            coverage=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb')))

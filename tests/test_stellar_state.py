"""Native lookup and motion contracts; constructed rows, not catalogue accuracy."""
from dataclasses import replace
from math import sqrt
import unittest
from unittest.mock import patch

from wenu_kernel import Kernel
from wenu_kernel.conformance import ProviderActivity, ProviderCase, ProviderConformance
from wenu_kernel.errors import ClosedSession, InvalidQuery, UnsupportedCapability
from wenu_kernel.records import AccuracyRequest, SessionPolicy, StateQuery, TimePoint
from wenu import stellar_state as bridge
import json
import pandas as pd
import pytest
from stellar_catalogue_fixtures import native_table
from wenu.stellar_catalogue import (
    METADATA_KEY, StellarCatalogueMetadata, ingest_stellar_catalogue,
    source_stellar_metadata, stellar_table_metadata,
)

# Explicit synthetic fixture epoch, not a production catalogue default.
HIPPARCOS_SOURCE_EPOCH = TimePoint(2448349, 0.0625, 'tt')


def test_packaged_metadata_supports_single_component_namespace_traversal(monkeypatch):
    """Python 3.11 namespace readers accept one child per joinpath call."""
    from importlib.resources import files
    from wenu import stellar_catalogue
    root = files('wenu.data.catalogs')
    class SingleComponentPath:
        def __init__(self, path):
            self.path = path
        def joinpath(self, child):
            return SingleComponentPath(self.path.joinpath(child))
        def read_text(self):
            return self.path.read_text()
    monkeypatch.setattr(stellar_catalogue, 'files', lambda package: SingleComponentPath(root))
    result = stellar_catalogue.packaged_stellar_metadata('hipparcos')
    expected = json.loads(root.joinpath('hipparcos').joinpath('metadata.json').read_text())
    assert result.to_record() == expected
    assert result.source_epoch.scale == expected['epoch']['scale']


def test_catalogue_metadata_controls_kernel_and_all_native_outputs(monkeypatch, tmp_path):
    from wenu.objects.stars import Stars
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    from wenu_kernel import KernelSession
    stars = Stars(None)
    table = native_table(pd.DataFrame(dict(ra_degrees=[15., 30.], dec_degrees=[20., 25.],
                                         magnitude=[1., 2.]), index=[100, 200]), epoch=2016.)
    record = table.attrs[METADATA_KEY]
    record['edition'] = 'synthetic-2016'
    record['provenance'] = ['independent synthetic metadata']
    record['source_metadata']['extra_source_field'] = ['preserve', {'nested': 42}]
    table = ingest_stellar_catalogue(table, StellarCatalogueMetadata.from_record(record)).table
    stars.source_catalog = stars.catalog = table
    seen = []
    evaluate = KernelSession.evaluate
    def capture(session, query):
        result = evaluate(session, query)
        seen.append(result)
        return result
    monkeypatch.setattr(KernelSession, 'evaluate', capture)
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.constellation_labels import ConstellationLabels
    graph = tmp_path / 'synthetic.fab'
    graph.write_text('Ari 2 100 200\n')
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    outputs = (stars.position(), stars.native_positions([100]), stars.realize(context, None),
               ConstellationLines(stars, filename=graph).realize(context, None),
               ConstellationLabels(stars, min_stars=1).realize(context, None),
               ConstellationLabels(stars, selected={'ZZZ'}).realize(context, None))
    for output in outputs:
        assert output.coordinate_spec.epoch == 'J2016'
        assert output.coordinate_spec.provenance == ('independent synthetic metadata',)
    metadata = stellar_table_metadata(table)
    assert all(batch.states[0].source_epoch == metadata.source_epoch for batch in seen)
    assert metadata.source_epoch == TimePoint(2457389., 0., 'tt')
    assert metadata.to_record() == record
    record['epoch']['value'] = 1900.
    assert metadata.epoch_label == 'J2016'


@pytest.mark.parametrize('field', ('epoch', 'frame', 'origin', 'units', 'edition', 'provenance', 'source_sha256'))
def test_catalogue_missing_required_metadata_is_refused(field):
    table = native_table(pd.DataFrame(dict(ra_degrees=[15.], dec_degrees=[20.]), index=[100]))
    record = table.attrs[METADATA_KEY]
    del record[field]
    with pytest.raises(ValueError, match='metadata'):
        StellarCatalogueMetadata.from_record(record)


@pytest.mark.parametrize('fault', ('missing_epoch', 'epoch_mismatch', 'missing_unit', 'duplicate_id', 'wrong_frame', 'wrong_angle_unit', 'source_epoch_conflict', 'missing_time_scale'))
def test_catalogue_inconsistent_astrometry_is_refused(fault):
    table = native_table(pd.DataFrame(dict(ra_degrees=[15., 30.], dec_degrees=[20., 25.]), index=[100, 200]))
    record = table.attrs[METADATA_KEY]
    if fault == 'missing_epoch': table = table.drop(columns=['epoch_year'])
    if fault == 'epoch_mismatch': table.loc[200, 'epoch_year'] = 2000.
    if fault == 'missing_unit': del record['units']['epoch_year']
    if fault == 'duplicate_id': table.index = [100, 100]
    if fault == 'wrong_frame': record['frame'] = 'fk5'
    if fault == 'wrong_angle_unit': record['units']['ra_degrees'] = 'rad'
    if fault == 'source_epoch_conflict': record['source_metadata']['reference_epoch_jd'] = 2451545.
    if fault == 'missing_time_scale': del record['epoch']['scale']
    with pytest.raises(ValueError):
        ingest_stellar_catalogue(table, StellarCatalogueMetadata.from_record(record))


def test_catalogue_source_identity_checked_before_publication(tmp_path, monkeypatch):
    from wenu.objects.stars import Stars
    table = native_table(pd.DataFrame(dict(ra_degrees=[15.], dec_degrees=[20.]), index=[100]))
    stars = Stars(None)
    stars.source_catalog = stars.catalog = table
    path = tmp_path / 'custom.dat'
    path.write_bytes(b'wrong bytes')
    def forbidden(*args):
        raise AssertionError('Unidentified source reached the parser')
    monkeypatch.setattr('wenu.objects.stars.hipparcos.load_dataframe', forbidden)
    with pytest.raises(ValueError, match='Source bytes differ'):
        stars.load(filename=path, metadata=table.attrs[METADATA_KEY])
    assert stars.source_catalog is stars.catalog is table
    bare = table.copy(); bare.attrs.clear()
    with pytest.raises(ValueError, match='ingest it before use'):
        stellar_table_metadata(bare)


def test_catalogue_sidecar_and_unknown_source_metadata_are_preserved(tmp_path):
    from hashlib import sha256
    table = native_table(pd.DataFrame(dict(ra_degrees=[15.], dec_degrees=[20.]), index=[100]))
    record = table.attrs[METADATA_KEY]
    payload = b'explicit custom catalogue bytes'
    record['source_sha256'] = sha256(payload).hexdigest()
    record['source_metadata']['publication'] = {'doi': 'synthetic:fixture'}
    path = tmp_path / 'custom.dat'
    path.with_name(path.name + '.metadata.json').write_text(json.dumps(record))
    metadata = source_stellar_metadata('hipparcos', payload, path)
    normalized = ingest_stellar_catalogue(table, metadata)
    assert normalized.table.attrs[METADATA_KEY] == record
    assert normalized.metadata.to_record() == record


class TrackedProvider(bridge.LegacyNativeStellarProvider):
    def __init__(self, rows):
        self.work = self.closes = 0
        super().__init__(rows, namespace="synthetic", source_epoch=HIPPARCOS_SOURCE_EPOCH,
                         provenance=("constructed native lookup fixture",))

    def _direction(self, key):
        self.work += 1
        return super()._direction(key)

    def close(self):
        self.closes += 1
        super().close()


def make_case():
    source = [["a", 0.0, 0.0], ["b", 90.0, 30.0]]
    provider = TrackedProvider(source)
    admission = provider.describe().admissions[0]
    # Different sample times test a static LOOKUP, never epoch propagation.
    query = StateQuery(admission.catalogue, admission.model, admission.objects,
                       (HIPPARCOS_SOURCE_EPOCH, TimePoint(2451545, 0.0, "tt")),
                       admission.reference, AccuracyRequest())
    probe = replace(query, times=(TimePoint(2460000, 0.0, "tt"),))

    def mutate():
        source[0][1] = 180.0
        source.append(["c", 45.0, 0.0])

    return ProviderCase(provider, query, probe,
                        lambda: ProviderActivity(provider.work, 0, provider.closes), mutate)


class TestNativeStellarConformance(ProviderConformance, unittest.TestCase):
    make_case = staticmethod(make_case)


class TestNativeStellarAdapter(unittest.TestCase):
    def test_analytic_vectors_source_epoch_and_unknown_uncertainty(self):
        rows = [("a", 0.0, 0.0), ("b", 90.0, 0.0), ("c", 225.0, -30.0), ("d", 0.0, 90.0)]
        states = bridge.native_stellar_states(rows, namespace="synthetic",
            source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("constructed analytic axes",))
        expected = ((1, 0, 0), (0, 1, 0), (-sqrt(6)/4, -sqrt(6)/4, -.5), (0, 0, 1))
        self.assertEqual(bridge.native_stellar_angles(states, rows),
                         tuple((lon, lat) for _, lon, lat in rows))
        for state, vector in zip(states, expected):
            self.assertEqual(state.source_epoch, HIPPARCOS_SOURCE_EPOCH)
            self.assertEqual(state.time, state.source_epoch)
            self.assertEqual(state.source_epoch.jd1 + state.source_epoch.jd2,
                             2451545.0 - 8.75 * 365.25)
            self.assertEqual(state.source_epoch.scale, "tt")
            self.assertEqual(state.reference.status, "native-catalogue")
            for actual, target in zip(state.vector, vector):
                self.assertAlmostEqual(actual, target, delta=1e-15)
            for channel in (state.evidence.measurement, state.evidence.physical_model, state.evidence.numerical):
                self.assertEqual((channel.status, channel.value), ("not_evaluated", None))

    def test_fixed_lookup_cannot_claim_motion_accuracy_or_certification(self):
        case = make_case(); provider = case.provider
        self.addCleanup(provider.close)
        admission = provider.describe().admissions[0]
        self.assertNotIn("epoch_direction", admission.capabilities)
        self.assertIn("native_direction", admission.capabilities)
        states = provider.evaluate(case.query).states
        self.assertEqual(states[0].vector, states[2].vector)
        self.assertTrue(all(s.source_epoch == HIPPARCOS_SOURCE_EPOCH for s in states))
        for query in (replace(case.query, accuracy=AccuracyRequest(angular_rad=1e-6)),
                      replace(case.query, evaluation_policy="bounded_reuse"),
                      replace(case.query, require_velocity=True)):
            with self.subTest(query=query):
                self.assertFalse(provider.supports(query).supported)
                with self.assertRaises(UnsupportedCapability):provider.evaluate(query)

    def test_input_change_changes_binding_and_original_buffers_do_not_alias(self):
        source = [["a", 12.0, -34.0]]
        first = TrackedProvider(source); original = first.describe()
        admission = original.admissions[0]
        query = StateQuery(admission.catalogue, admission.model, admission.objects,
                           (HIPPARCOS_SOURCE_EPOCH,), admission.reference, AccuracyRequest())
        before = first.evaluate(query)
        source[0][1] = 56.0
        second = TrackedProvider(source)
        self.addCleanup(first.close);self.addCleanup(second.close)
        self.assertEqual(first.describe(), original)
        self.assertNotEqual(original.catalogues, second.describe().catalogues)
        self.assertEqual(first.evaluate(query), before)
        self.assertEqual(first.work, 2)
        self.assertEqual(second.work, 0)

    def test_invalid_rows_do_not_fabricate_kernel_states(self):
        for rows in ([('a', float('nan'), 0.0)], [('a', 0.0, 91.0)],
                     [('a', True, 0.0)], [('a', 0.0, 0.0), ('a', 1.0, 0.0)]):
            with self.subTest(rows=rows), self.assertRaises(InvalidQuery):
                TrackedProvider(rows)

    def test_owned_service_closes_once_after_success_and_evaluation_failure(self):
        created = []
        original = bridge.LegacyNativeStellarProvider
        class Provider(original):
            def __init__(self, *args, **kwargs):
                self.closes = 0; created.append(self);super().__init__(*args, **kwargs)
            def close(self):self.closes += 1;super().close()
        for fail in (False, True):
            with self.subTest(fail=fail), patch.object(bridge, "LegacyNativeStellarProvider", Provider):
                if fail:
                    with patch.object(Provider, "evaluate", side_effect=RuntimeError("synthetic backend failure")):
                        with self.assertRaisesRegex(Exception, "evaluate failed"):
                            bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                                source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
                else:
                    bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                        source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
                self.assertEqual(created[-1].closes, 1)
                with self.assertRaises(ClosedSession):created[-1].describe()

    def test_failed_registration_and_empty_tables_retain_caller_cleanup(self):
        with patch.object(bridge.LegacyNativeStellarProvider, "close", autospec=True) as close:
            self.assertEqual(bridge.native_stellar_states([], namespace="synthetic",
                source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",)), ())
            self.assertEqual(close.call_count, 1)
        with patch.object(Kernel, "register", side_effect=RuntimeError("synthetic registration failure")), \
                patch.object(bridge.LegacyNativeStellarProvider, "close", autospec=True) as close:
            with self.assertRaisesRegex(RuntimeError, "registration failure"):
                bridge.native_stellar_states([('a', 0., 0.)], namespace="synthetic",
                    source_epoch=HIPPARCOS_SOURCE_EPOCH, provenance=("synthetic",))
            self.assertEqual(close.call_count, 1)


@pytest.fixture
def motion_source():
    """Small self-contained synthetic snapshot; no real catalogue or network."""
    from collections import Counter
    from hashlib import sha256
    from pathlib import Path
    from wenu.stellar_enrichment import StellarEnrichmentSnapshot, PRODUCTS, encode, identity
    def build(change=None, *, epoch=2016., original_v=2., edr3=False,
              hip2_change=None, hip2_hips=(5,), hip2_epoch=1991.25, hip2_scale=None):
        sources = []
        for i in (1, 2, 3, 4, 6, 7, 8):
            src = dict(source_id=str(9007199254740992+i), solution_id='9007199254740999',
                ra=0., dec=90. if i==6 else 0., ref_epoch=epoch, parallax=100.,
                pmra=1000., pmdec=2000., radial_velocity=30.,
                astrometric_params_solved=95 if i in (2,6) else 31,
                ruwe=8.5, duplicated_source=True, phot_g_mean_mag=12., ra_dec_corr=.4)
            if i==2: src['radial_velocity']=None
            if i==3: src['parallax']=-1.
            if i==4: src.update(astrometric_params_solved=3, pmra=None, pmdec=None)
            if i==7: src['astrometric_params_solved']=999
            if i==8: src['parallax']=0.
            if i==1 and change: src.update(change)
            sources.append(src)
        gaia={str(i):s for i,s in zip((1,2,3,4,6,7,8),sources)}
        # One unassociated entry has a complete Hip2 source record, whose
        # unresolved time convention cannot be silently upgraded to motion.
        profile=json.loads((Path(__file__).parents[1]/'docs/developer/data/stellar_astrometry_acquisition_v1.json').read_text())['hipparcos2']
        profile['reference']['epoch'].update(value=hip2_epoch,scale=hip2_scale)
        hip_rows=[]
        for number in hip2_hips:
            h=dict(HIP=str(number),Sn=5,So=0,Nc=1,RArad=.2,DErad=-.3,Plx=10.,pmRA=0.,pmDE=1.,
                   e_RArad=1.,e_DErad=1.,e_Plx=1.,e_pmRA=1.,e_pmDE=1.,UW=[1.]*15)
            h.update(hip2_change or {})
            native=bytearray(b' '*276)
            for name,spec in profile['columns'].items():
                a,b=spec['first_byte']-1,spec['last_byte']
                raw=(''.join(f'{v:7.2f}'for v in h[name])if name=='UW'else
                     (''if h[name]is None else str(h[name])).rjust(b-a))
                native[a:b]=raw.encode()
            h.update(original_record_ascii=native.decode(),record_sha256=sha256(native).hexdigest())
            hip_rows.append(h)
        hip_map={r['HIP']:r for r in hip_rows}
        stars=[]; candidates=[]; photometry=[]; choices=Counter()
        for i in range(1,10):
            hip=str(i); src=gaia.get(hip)
            link=(dict(hip=hip,catalogue='Gaia',release='DR3',source_id=src['source_id'])if src else None)
            choice=('gaia'if src and src['astrometric_params_solved']in(31,95)and
                all(src.get(k)is not None for k in ('ra','dec','ref_epoch','parallax','pmra','pmdec'))
                else 'hipparcos2'if str(i)in hip_map and all(hip_map[str(i)].get(k)is not None
                    for k in ('RArad','DErad','Plx','pmRA','pmDE'))else 'original_1997_lookup')
            if edr3 and i==1:
                link.update(release='EDR3',equivalent_dr3_identity=dict(release='DR3',source_id=src['source_id'],
                    bridge={'policy':'ESA-explicit-identical-source-list'}))
            original=dict(hip=hip,magnitude=original_v if i==1 else None, designation={'names':['Synthetic star']})
            row=dict(schema='wenu-stellar-enrichment/1',
                identity=dict(catalogue='hipparcos',edition='synthetic-1997',identifier=hip,component=None),
                original=original,published_association=link,match_status='identified'if link else'unmatched',
                adopted_solution=None,input_availability=dict(model_adopted=False,preferred_available_input=choice),
                candidates=[src['source_id']]if src else [],source_references=dict(gaia=src['source_id']if src else None,
                    hipparcos2=hip if hip in hip_map else None),foreign_photometry={'phot_g_mean_mag':src['phot_g_mean_mag']}if src else None)
            stars.append(row);choices[choice]+=1
            photometry.append([i,'missing'if original['magnitude']is None else float(original['magnitude']).hex()])
            if src: candidates.append(dict(hip=hip,source_id=src['source_id']))
        baseline=dict(catalogue='hipparcos',edition='synthetic-1997',source_sha256='a'*64,rows=9,
            ordered_hip_ids_sha256=sha256(('\n'.join(map(str,range(1,10)))+'\n').encode()).hexdigest(),
            hip_magnitude_pairs_sha256=sha256(json.dumps(photometry,separators=(',',':')).encode()).hexdigest())
        units={'ra':'deg','dec':'deg','ref_epoch':'yr','parallax':'mas',
               'pmra':'mas / yr','pmdec':'mas / yr','radial_velocity':'km / s'}
        metadata=dict(schema='wenu-stellar-enrichment-metadata/1',row_schema='wenu-stellar-enrichment/1',
            model_admission='none',baseline=baseline,original_columns=list(stars[0]['original']),
            required_preserved_columns=['magnitude','designation'],
            original_metadata=dict(catalogue='hipparcos',edition='synthetic-1997',source_sha256='a'*64,
                frame='icrs',origin='solar-system-barycenter',epoch=dict(value=1991.25,format='jyear',scale='tt'),units={'magnitude':'mag'}),
            gaia_reference=dict(frame='icrs',origin='solar-system-barycenter',epoch_scale='tcb',release='DR3',
                right_ascension_motion='mu_alpha*cos(delta)',expected_ref_epoch=epoch),
            gaia_columns=list(sources[0]),gaia_column_units={k:units.get(k)for k in sources[0]},
            hipparcos2_profile=profile,
            original_rows_sha256=sha256(b''.join(encode(r['original'])+b'\n'for r in stars)).hexdigest(),
            association_ledger_sha256=sha256(b''.join(encode(dict(hip=r['identity']['identifier'],association=r['published_association']))+b'\n'for r in stars)).hexdigest(),
            counts=dict(retained_hip_rows=9,published_associations=7,gaia_source_rows=7,hipparcos2_rows=len(hip_rows),
                candidate_pairs=7,preferred_available_inputs=dict(choices)))
        values=[encode(metadata),*[b''.join(encode(r)+b'\n'for r in rs)for rs in (stars,sources,hip_rows,candidates)]]
        products=tuple(zip(PRODUCTS,values))
        manifest=encode(dict(schema='wenu-stellar-enrichment-snapshot/1',complete=True,
            products={name:identity(raw)for name,raw in products}))
        return StellarEnrichmentSnapshot(products,manifest)
    return build


def stellar_motion_case(source, *, representation='direction', coverage=None):
    from wenu_kernel.records import TimeSpan
    coverage=coverage or TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb'))
    catalogue=bridge.admit_stellar_motion(source,coverage=coverage,
        distance_policy='positive-parallax-reciprocal',radial_velocity_policy='spectroscopic-proxy')
    provider=bridge.StellarMotionProvider(catalogue,representation=representation)
    a=provider.describe().admissions[0]
    return catalogue,provider,StateQuery(a.catalogue,a.model,a.objects,
        (TimePoint(2457389,0,'tcb'),),a.reference,
        AccuracyRequest(metric='euclidean_norm')if representation=='cartesian'else AccuracyRequest())


def test_stellar_motion_admission_preserves_source_population_and_explicit_gaps(motion_source):
    """Protect source loss/zero filling; closest existing native input-copy test."""
    from dataclasses import FrozenInstanceError
    source=motion_source();before=source.products
    cat,p,q=stellar_motion_case(source)
    assert [r.identifier for r in cat.rows]==list(map(str,range(1,10)))
    assert [r.unavailable_reason for r in cat.rows]==[None,'missing_gaia_radial_velocity',
        'nonpositive_gaia_parallax','gaia_position_only','no_published_gaia_association',
        None,'unsupported_gaia_solution','nonpositive_gaia_parallax','no_published_gaia_association']
    assert cat.to_record()['counts']['full_input_models']==2
    objects=p.catalogue(q.catalogue).objects
    assert len(objects)==9 and [k.value for k in q.objects]==['hipparcos:1','hipparcos:6']
    assert objects[0].external_ids[1].identifier=='9007199254740993'
    assert objects[0].external_ids[1].edition=='DR3'
    assert cat.source is source and source.products==before
    assert cat.source.metadata['model_admission']=='none'
    assert next(cat.source.records())['original']['magnitude']==2.
    assert list(cat.source.records())[4]['source_references']['hipparcos2']=='5'
    detached=cat.to_record();detached['policies']['distance']='changed'
    assert cat.to_record()['policies']['distance']=='positive-parallax-reciprocal'
    with pytest.raises(FrozenInstanceError):cat.rows=()
    p.close()
    with pytest.raises(ClosedSession):p.describe()


@pytest.mark.parametrize('representation',['direction','cartesian'])
def test_stellar_motion_kernel_axis_oracle_and_order(motion_source,representation):
    """Independent equatorial axes protect SI scale, RA cosine and PM/RV signs."""
    import numpy as np
    from wenu_kernel.records import ObjectKey
    cat,p,q=stellar_motion_case(motion_source(),representation=representation)
    # The same source vector is at x; RA differential goes toward +y and Dec
    # toward +z. Expected scalar conversions are independent Astropy units.
    from astropy import units as u
    d=(10*u.pc).to_value(u.m);year=(1*u.yr).to_value(u.s)
    velocity=(30000.,d*(1*u.arcsec).to_value(u.rad)/year,d*(2*u.arcsec).to_value(u.rad)/year)
    np.testing.assert_allclose(cat.rows[0].position_m,(d,0,0),rtol=4e-16,atol=0)
    np.testing.assert_allclose(cat.rows[0].velocity_m_s,velocity,rtol=4e-16,atol=0)
    t=TimePoint(2457754,.25,'tcb')
    q=replace(q,objects=(ObjectKey('hipparcos:6'),ObjectKey('hipparcos:1')),times=(t,))
    with Kernel(references=(q.reference,))as k:
        k.register(p,ownership='owned')
        with k.open_session(SessionPolicy((q.catalogue,)))as s:
            batch=s.evaluate(q)
    assert [r.object_key for r in batch.states]==list(q.objects)
    expected=np.array((d,0,0))+np.array(velocity)*year
    state=batch.states[1]
    assert state.source_epoch==TimePoint(2457389,0,'tcb') and state.time==state.anchor_time==t
    if representation=='direction':
        np.testing.assert_allclose(state.vector,expected/np.linalg.norm(expected),rtol=1e-14,atol=1e-16)
        assert state.evidence.numerical.value==2**-40
    else:
        np.testing.assert_allclose(state.position_m,expected,rtol=1e-14,atol=1.)
        np.testing.assert_allclose(state.velocity_m_s,velocity,rtol=4e-16,atol=0)
        assert state.velocity_evidence.numerical.status=='not_evaluated'
    evidence=state.position_evidence if representation=='cartesian'else state.evidence
    assert evidence.measurement.status==evidence.physical_model.status=='not_evaluated'
    with pytest.raises(ClosedSession):p.describe()


@pytest.mark.parametrize('ra,dec',[(123.,-45.),(359.9,89.999999),(10.,-90.)])
def test_stellar_motion_source_conversion_matches_independent_spherical_differential(motion_source,ra,dec):
    import numpy as np
    from astropy import units as u
    from astropy.coordinates import (SphericalRepresentation,SphericalCosLatDifferential,
                                     CartesianRepresentation,CartesianDifferential)
    cat,p,q=stellar_motion_case(motion_source(dict(ra=ra,dec=dec,pmra=-111.,pmdec=23.,radial_velocity=-44.)))
    independent=SphericalRepresentation(ra*u.deg,dec*u.deg,10*u.pc,
        differentials=SphericalCosLatDifferential(-111*u.mas/u.yr,23*u.mas/u.yr,-44*u.km/u.s))
    cart=independent.represent_as(CartesianRepresentation,CartesianDifferential)
    np.testing.assert_allclose(cat.rows[0].position_m,cart.xyz.to_value(u.m),rtol=2e-15,atol=30.)
    np.testing.assert_allclose(cat.rows[0].velocity_m_s,cart.differentials['s'].d_xyz.to_value(u.m/u.s),rtol=2e-15,atol=2e-10)
    p.close()


@pytest.mark.parametrize('change,reason',[
    ({'radial_velocity':None},'missing_gaia_radial_velocity'),
    ({'pmra':None},'missing_gaia_pmra'),({'parallax':None},'missing_gaia_parallax'),
    ({'parallax':0.},'nonpositive_gaia_parallax'),({'parallax':-1.},'nonpositive_gaia_parallax'),
    ({'astrometric_params_solved':95,'radial_velocity':None},'missing_gaia_radial_velocity'),
])
def test_stellar_motion_incomplete_or_nonpositive_inputs_are_not_invented(motion_source,change,reason):
    from wenu_kernel.records import ObjectKey
    cat,p,q=stellar_motion_case(motion_source(change))
    assert cat.rows[0].unavailable_reason==reason
    assert cat.rows[0].position_m is cat.rows[0].velocity_m_s is None
    assert len(p.catalogue(q.catalogue).objects)==9
    bad=replace(q,objects=(ObjectKey('hipparcos:1'),))
    assert not p.supports(bad).supported
    with pytest.raises(UnsupportedCapability):p.evaluate(bad)
    p.close()


@pytest.mark.parametrize('fault',['wrong_scale','outside','unknown','unavailable','source_binding','subfloor','velocity'])
def test_stellar_motion_refuses_invalid_queries_after_success(motion_source,fault):
    from wenu_kernel.records import ObjectKey
    cat,p,q=stellar_motion_case(motion_source())
    assert p.evaluate(q).states
    if fault=='wrong_scale':bad=replace(q,times=(TimePoint(2457389,0,'tt'),))
    if fault=='outside':bad=replace(q,times=(TimePoint(2500001,0,'tcb'),))
    if fault=='unknown':bad=replace(q,objects=(ObjectKey('hipparcos:999'),))
    if fault=='unavailable':bad=replace(q,objects=(ObjectKey('hipparcos:2'),))
    if fault=='source_binding':
        _,other,_=stellar_motion_case(motion_source(original_v=3.))
        bad=replace(q,catalogue=other.describe().admissions[0].catalogue);other.close()
    if fault=='subfloor':bad=replace(q,accuracy=AccuracyRequest(angular_rad=2**-41))
    if fault=='velocity':bad=replace(q,require_velocity=True)
    assert not p.supports(bad).supported
    with pytest.raises(UnsupportedCapability):p.evaluate(bad)
    assert p.evaluate(q).states
    p.close()


@pytest.mark.parametrize('fault',['domain','scale','distance','rv','source','representation'])
def test_stellar_motion_admission_refuses_unsupported_context(motion_source,fault):
    from wenu_kernel.records import TimeSpan
    source=motion_source()
    kwargs=dict(coverage=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb')),
                distance_policy='positive-parallax-reciprocal',radial_velocity_policy='spectroscopic-proxy')
    if fault=='domain':kwargs['coverage']=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2400001,0,'tcb'))
    if fault=='scale':kwargs['coverage']=TimeSpan(TimePoint(2400000,0,'tt'),TimePoint(2500000,0,'tt'))
    if fault=='distance':kwargs['distance_policy']='invented Bayesian distance'
    if fault=='rv':kwargs['radial_velocity_policy']='missing-is-zero'
    if fault=='source':source={}
    if fault=='representation':
        cat=bridge.admit_stellar_motion(source,**kwargs)
        with pytest.raises(ValueError):bridge.StellarMotionProvider(cat,representation='observed')
    else:
        with pytest.raises(ValueError):bridge.admit_stellar_motion(source,**kwargs)


def test_stellar_motion_source_epoch_and_model_identity_are_not_hard_coded(motion_source):
    cat,p,q=stellar_motion_case(motion_source(epoch=2015.5))
    assert cat.rows[0].source_epoch==TimePoint(2457206,.375,'tcb')
    original,other,_=stellar_motion_case(motion_source())
    assert p.describe().admissions[0].model!=other.describe().admissions[0].model
    assert cat.source.metadata['gaia_reference']['expected_ref_epoch']==2015.5
    p.close();other.close()


@pytest.mark.parametrize('motion_kind',['full','angular','hip2'])
def test_stellar_motion_provider_passes_sdk_conformance_and_reuse(motion_source,motion_kind):
    """Reuse/lifetime uses inherited core, while bindings come from real adapter."""
    import io
    from wenu_kernel.conformance import provider_suite
    def factory():
        case=stellar_hip2_case if motion_kind=='hip2'else stellar_angular_case if motion_kind=='angular'else stellar_motion_case
        cat,p,q=case(motion_source())
        q=replace(q,times=(TimePoint(2457389,0,'tcb'),TimePoint(2457389,.01,'tcb')))
        probe=replace(q,times=(TimePoint(2457389,.1,'tcb'),))
        counts=dict(evaluate=0,certify=0,close=0)
        evaluate,certify,close=p.evaluate,p.certify,p.close
        def measured(q):counts['evaluate']+=1;return evaluate(q)
        def certified(q,a):counts['certify']+=1;return certify(q,a)
        def closed():counts['close']+=1;return close()
        p.evaluate,p.certify,p.close=measured,certified,closed
        def mutate():
            record=next(cat.source.records());record['published_association']['source_id']='1'
            meta=cat.to_record();meta['policies']['distance']='changed'
        reuse=replace(q,evaluation_policy='bounded_reuse',
                      accuracy=AccuracyRequest(angular_rad=1e-5))
        return ProviderCase(p,q,probe,lambda:ProviderActivity(counts['evaluate'],counts['certify'],counts['close']),mutate,reuse)
    result=unittest.TextTestRunner(stream=io.StringIO()).run(provider_suite(factory,name='StellarFullInputs'))
    assert result.wasSuccessful(),result.errors+result.failures
    assert result.testsRun==8 and not result.skipped


def test_stellar_motion_cold_source_reload_and_query_without_science_stack(motion_source,tmp_path):
    """Protect eager facade/provider/graphics dependencies and hidden source I/O."""
    import shutil,subprocess,sys
    from pathlib import Path
    import wenu_kernel
    root=Path(__file__).parents[1]
    isolated=tmp_path/'isolated';isolated.mkdir()
    package=isolated/'wenu';package.mkdir();(package/'__init__.py').write_text('')
    for name in ('stellar_state','catalogue_state','stellar_enrichment','astrometric_state','astrometric_coordinates'):
        shutil.copyfile(root/'src/wenu'/f'{name}.py',package/f'{name}.py')
    shutil.copytree(Path(wenu_kernel.__file__).parent,isolated/'wenu_kernel',ignore=shutil.ignore_patterns('__pycache__'))
    source=motion_source();snapshot=tmp_path/'snapshot_v1';snapshot.mkdir()
    for name,payload in source.products:(snapshot/name).write_bytes(payload)
    (snapshot/'source_manifest_v1.json').write_bytes(source.manifest)
    script='''
import sys,socket,shutil,importlib.abc
sys.path.insert(0,sys.argv[1])
def forbidden(*a,**k):raise AssertionError('network forbidden')
socket.socket=forbidden
class BlockScience(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.split('.')[0] in ('astropy','numpy','pandas','skyfield','matplotlib') or fullname.startswith(('wenu.observer','wenu.sky','wenu.objects','wenu.rendering')):
   raise AssertionError('native ancient query must not import '+fullname)
sys.meta_path.insert(0,BlockScience())
from wenu.stellar_enrichment import load_stellar_enrichment
from wenu.stellar_state import admit_stellar_motion,admit_stellar_angular_motion,admit_stellar_hipparcos2_motion,StellarMotionProvider
from wenu_kernel import Kernel
from wenu_kernel.records import TimePoint,TimeSpan,StateQuery,AccuracyRequest,SessionPolicy
from wenu_kernel.time import TimeService
from wenu.astrometric_coordinates import HistoricalDate,resolve_historical_date,TcbTdbAdapter
date=HistoricalDate(year=1000,month=1,day=1,year_numbering='bce',calendar='julian',scale='tdb',uncertainty_s=None)
adapter=TcbTdbAdapter(TimeSpan(TimePoint(1000000,0,'tdb'),TimePoint(3000000,0,'tdb')))
historical=resolve_historical_date(date,time_service=TimeService((adapter,),admissions=(adapter.describe(),)))
assert historical.source.uncertainty_s is None and historical.source.astronomical_year==-999
source=load_stellar_enrichment(sys.argv[2])
c=admit_stellar_motion(source,coverage=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb')),
 distance_policy='positive-parallax-reciprocal',radial_velocity_policy='spectroscopic-proxy')
angular=admit_stellar_angular_motion(source,coverage=TimeSpan(TimePoint(-15000000,0,'tcb'),TimePoint(20000000,0,'tcb')))
hip2=admit_stellar_hipparcos2_motion(source,coverage=TimeSpan(TimePoint(-15000000,0,'tcb'),TimePoint(20000000,0,'tcb')),
 epoch_policy='nominal-tcb-deferred-qualification')
shutil.rmtree(sys.argv[2])
for catalogue,representation,expected in ((c,'direction',2),(c,'cartesian',2),(angular,'direction',5),(hip2,'direction',1)):
 p=StellarMotionProvider(catalogue,representation=representation);a=p.describe().admissions[0]
 times=(TimePoint(2457389,0,'tcb'),) if catalogue is c else (historical.time,)
 q=StateQuery(a.catalogue,a.model,a.objects,times,a.reference,
  AccuracyRequest(metric='euclidean_norm')if representation=='cartesian'else AccuracyRequest())
 with Kernel(references=(a.reference,))as k:
  k.register(p,ownership='owned')
  with k.open_session(SessionPolicy((a.catalogue,)))as s:
   states=s.evaluate(q).states
   assert len(states)==expected and all(row.time==times[0] for row in states)
assert not any(name.split('.')[0]in('astropy','numpy','pandas','skyfield','matplotlib')for name in sys.modules)
assert not any(name.startswith(('wenu.objects','wenu.sky','wenu.rendering'))for name in sys.modules)
print('cold source-to-kernel admission passed')
'''
    result=subprocess.run([sys.executable,'-I','-S','-c',script,str(isolated),str(snapshot)],
                          text=True,capture_output=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    assert 'cold source-to-kernel admission passed'in result.stdout


def test_stellar_motion_preserves_published_edr3_and_bridged_dr3_external_ids(motion_source):
    cat,p,q=stellar_motion_case(motion_source(edr3=True))
    ids=p.catalogue(q.catalogue).objects[0].external_ids
    assert [(i.catalogue,i.edition,i.identifier)for i in ids]==[
        ('hipparcos','synthetic-1997','1'),('Gaia','EDR3','9007199254740993'),('Gaia','DR3','9007199254740993')]
    assert next(cat.source.records())['published_association']['release']=='EDR3'
    p.close()


def stellar_angular_case(source, *, coverage=None):
    from wenu_kernel.records import TimeSpan
    epoch=bridge._stellar_epoch(source.metadata['gaia_reference']['expected_ref_epoch'],'tcb')
    coverage=coverage or TimeSpan(TimePoint(epoch.jd1-18262500,epoch.jd2,'tcb'),TimePoint(epoch.jd1+18262500,epoch.jd2,'tcb'))
    catalogue=bridge.admit_stellar_angular_motion(source,coverage=coverage)
    provider=bridge.StellarMotionProvider(catalogue)
    a=provider.describe().admissions[0]
    return catalogue,provider,StateQuery(a.catalogue,a.model,a.objects,
        (catalogue.rows[0].source_epoch,),a.reference,AccuracyRequest())


def test_stellar_angular_admission_retains_unknown_inputs_and_full_model_bindings(motion_source):
    """Protect silent zero filling/adoption; closest full-input source-preservation test."""
    from hashlib import sha256
    source=motion_source();original=source.products
    full,fp,fq=stellar_motion_case(source)
    angular,ap,aq=stellar_angular_case(source)
    assert sha256(full.metadata_json).hexdigest()=='96f0acec6ae9d826d90aa661442bb6e1e0886a56b5b5938c5b8f85919ac45229'
    assert fp.describe().admissions[0].model.configuration_digest=='2ef257cbff0465eaab84c45bf7e10399543664a5d86f8bbc6115917e262c1ccf'
    assert angular.source is source and source.products==original
    assert angular.to_record()['counts']==dict(retained_objects=9,angular_models=5,
        unavailable_by_reason={'gaia_position_only':1,'no_published_gaia_association':2,'unsupported_gaia_solution':1})
    assert [k.value for k in aq.objects]==['hipparcos:1','hipparcos:2','hipparcos:3','hipparcos:6','hipparcos:8']
    assert len(ap.catalogue(aq.catalogue).objects)==9
    assert len(fp.catalogue(fq.catalogue).objects)==9
    assert all(type(r)is bridge.AngularMotionRow for r in angular.rows)
    assert not hasattr(angular.rows[1],'position_m')and not hasattr(angular.rows[1],'velocity_m_s')
    gaia=list(source.records('gaia_sources_v1.jsonl'))
    assert gaia[1]['radial_velocity']is None and gaia[2]['parallax']==-1 and gaia[6]['parallax']==0
    assert aq.catalogue!=fq.catalogue and aq.model!=fq.model and aq.reference!=fq.reference
    assert next(source.records())['original']['magnitude']==2.
    assert next(source.records())['adopted_solution']is None
    assert angular.to_record()['policies']['perspective']=='omitted'
    fp.close();ap.close()


@pytest.mark.parametrize('changes',[{'parallax':None,'radial_velocity':None},
    {'parallax':-5.,'radial_velocity':None},{'parallax':0.,'radial_velocity':None},
    {'parallax':500.,'radial_velocity':-2000.}])
def test_stellar_angular_math_is_independent_of_unused_distance_and_rv(motion_source,changes):
    first,p,q=stellar_angular_case(motion_source())
    other,op,oq=stellar_angular_case(motion_source(changes))
    assert first.rows==other.rows
    assert first.to_record()['angular_solutions_sha256']==other.to_record()['angular_solutions_sha256']
    # Retained source identity still distinguishes changed supplied facts.
    assert q.catalogue!=oq.catalogue and q.model!=oq.model
    assert p.evaluate(q).states[0].vector==op.evaluate(oq).states[0].vector
    p.close();op.close()


@pytest.mark.parametrize('days',[-18262500,-365.25,0.,365.25,18262500])
def test_stellar_angular_short_long_epoch_analytic_direction_oracle(motion_source,days):
    from math import floor,hypot
    from astropy import units as u
    cat,p,q=stellar_angular_case(motion_source())
    epoch=cat.rows[0].source_epoch
    whole=floor(epoch.jd2+days+.5)
    time=TimePoint(epoch.jd1+whole,epoch.jd2+days-whole,'tcb')
    q=replace(q,objects=(q.objects[0],),times=(time,))
    with Kernel(references=(q.reference,))as kernel:
        kernel.register(p,ownership='owned')
        with kernel.open_session(SessionPolicy((q.catalogue,)))as session:state=session.evaluate(q).states[0]
    # Equatorial analytic normal triad: east=y, north=z. Unit conversion is
    # independently supplied by Astropy, without a mock distance or RV.
    x,y,z=1.,(days*u.day*(1*u.arcsec/u.yr)).to_value(u.rad),(days*u.day*(2*u.arcsec/u.yr)).to_value(u.rad)
    norm=hypot(x,y,z)
    assert max(abs(v-w/norm)for v,w in zip(state.vector,(x,y,z)))<2e-15
    assert state.source_epoch==epoch and state.time==state.anchor_time==time
    assert state.evidence.measurement.status==state.evidence.physical_model.status=='not_evaluated'
    assert state.evidence.numerical.value==2**-40
    # The long result is the declared normalized tangent model, not a
    # constant-angular-speed rotation or repeated incremental re-anchoring.


@pytest.mark.parametrize('changes,reason',[({'pmra':None},'missing_gaia_pmra'),
    ({'pmra':None,'pmdec':None},'missing_gaia_pmra,pmdec'),
    ({'astrometric_params_solved':3},'gaia_position_only'),
    ({'astrometric_params_solved':999},'unsupported_gaia_solution')])
def test_stellar_angular_missing_pm_or_unqualified_solution_stays_unavailable(motion_source,changes,reason):
    from wenu_kernel.records import ObjectKey
    cat,p,q=stellar_angular_case(motion_source(changes))
    assert cat.rows[0].unavailable_reason==reason
    assert cat.rows[0].direction is cat.rows[0].tangent_per_s is None
    assert len(p.catalogue(q.catalogue).objects)==9
    with pytest.raises(UnsupportedCapability):p.evaluate(replace(q,objects=(ObjectKey('hipparcos:1'),)))
    p.close()


@pytest.mark.parametrize('ra,dec',[(359.999,89.999999),(10.,90.),(321.,-90.),(0.,0.)])
def test_stellar_angular_pole_wrap_zero_pm_and_unknown_distance_are_explicit(motion_source,ra,dec):
    from math import cos,sin,radians
    cat,p,q=stellar_angular_case(motion_source(dict(ra=ra,dec=dec,pmra=0.,pmdec=0.,parallax=None,radial_velocity=None)))
    row=cat.rows[0]
    assert row.unavailable_reason is None and row.tangent_per_s==(0,0,0)
    late=TimePoint(2451545+18000000,0,'tcb')
    q=replace(q,objects=(q.objects[0],),times=(q.times[0],late))
    states=p.evaluate(q).states
    assert states[0].vector==states[1].vector
    expected=(cos(radians(dec))*cos(radians(ra)),cos(radians(dec))*sin(radians(ra)),sin(radians(dec)))
    assert max(abs(a-b)for a,b in zip(states[0].vector,expected))<5e-16
    p.close()


@pytest.mark.parametrize('fault',['cartesian','velocity','position_bound','scale','domain','unavailable','full_binding'])
def test_stellar_angular_capability_and_warm_refusal(motion_source,fault):
    from wenu_kernel.records import ObjectKey
    cat,p,q=stellar_angular_case(motion_source())
    baseline=p.evaluate(q)
    if fault=='cartesian':
        with pytest.raises(ValueError):bridge.StellarMotionProvider(cat,representation='cartesian')
    else:
        if fault=='velocity':bad=replace(q,require_velocity=True)
        if fault=='position_bound':bad=replace(q,accuracy=AccuracyRequest(position_m=1.,metric='euclidean_norm'))
        if fault=='scale':bad=replace(q,times=(TimePoint(2457389,0,'tt'),))
        if fault=='domain':bad=replace(q,times=(TimePoint(cat.coverage.stop.jd1+1,0,'tcb'),))
        if fault=='unavailable':bad=replace(q,objects=(ObjectKey('hipparcos:5'),))
        if fault=='full_binding':
            _,fp,fq=stellar_motion_case(motion_source());bad=replace(q,model=fq.model);fp.close()
        assert not p.supports(bad).supported
        with pytest.raises(UnsupportedCapability):p.evaluate(bad)
    assert p.evaluate(q)==baseline
    p.close()


@pytest.mark.parametrize('fault',['scale','epoch_outside','policy','distance'])
def test_stellar_angular_admission_context_refuses_without_inference(motion_source,fault):
    from wenu_kernel.records import TimeSpan
    source=motion_source()
    if fault=='scale':
        span=TimeSpan(TimePoint(2400000,0,'tt'),TimePoint(2500000,0,'tt'))
        with pytest.raises(ValueError):bridge.admit_stellar_angular_motion(source,coverage=span)
    elif fault=='epoch_outside':
        span=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2400001,0,'tcb'))
        with pytest.raises(ValueError):bridge.admit_stellar_angular_motion(source,coverage=span)
    else:
        span=TimeSpan(TimePoint(2400000,0,'tcb'),TimePoint(2500000,0,'tcb'))
        with pytest.raises(ValueError):bridge.StellarMotionCatalogue(source,span,
            'positive-parallax-reciprocal'if fault=='distance'else'not-used','not-used',
            'proper-motion-angular'if fault=='distance'else'invented-model')


def stellar_hip2_case(source, *, coverage=None):
    from wenu_kernel.records import TimeSpan
    coverage=coverage or TimeSpan(TimePoint(-16000000,0,'tcb'),TimePoint(21000000,0,'tcb'))
    cat=bridge.admit_stellar_hipparcos2_motion(source,coverage=coverage,
        epoch_policy='nominal-tcb-deferred-qualification')
    p=bridge.StellarMotionProvider(cat);a=p.describe().admissions[0]
    q=(StateQuery(a.catalogue,a.model,a.objects,(TimePoint(2448349,.0625,'tcb'),),a.reference,AccuracyRequest())
       if a.objects else None)
    return cat,p,q


def test_hip2_nominal_policy_preserves_source_and_separates_gaia_bindings(motion_source):
    """Protect relabelling original facts; extend prior all-HIP angular admission check."""
    from hashlib import sha256
    source=motion_source();before=source.products
    full,fp,fq=stellar_motion_case(source);gaia,gp,gq=stellar_angular_case(source)
    cat,p,q=stellar_hip2_case(source);record=cat.to_record()
    assert source.products==before and cat.source is source
    assert len(cat.rows)==len(p.catalogue(q.catalogue).objects)==9
    assert [k.value for k in q.objects]==['hipparcos:5']
    assert cat.rows[4].source_epoch==TimePoint(2448349,.0625,'tcb')
    assert source.metadata['hipparcos2_profile']['reference']['epoch']['scale']is None
    assert record['hipparcos2_reference']['epoch']['scale']is None
    assert record['model_reference']['epoch_scale']=='tcb'
    assert record['policies']['time_convention_error']=='not-evaluated'
    assert record['policies']['follow_up'].endswith('/326')
    assert record['counts']['angular_models']==1
    assert next(source.records())['adopted_solution']is None
    assert sha256(full.metadata_json).hexdigest()=='96f0acec6ae9d826d90aa661442bb6e1e0886a56b5b5938c5b8f85919ac45229'
    assert gaia.to_record()['angular_solutions_sha256']=='77882ffac3502df789859de3ff8552a6b1fffb3bfadbbc093ac00da1836c103b'
    assert len({q.catalogue,gq.catalogue,fq.catalogue})==3
    state=p.evaluate(q).states[0]
    assert state.evidence.measurement.status==state.evidence.physical_model.status=='not_evaluated'
    assert 'time-convention' in state.evidence.measurement.meaning
    obj=p.catalogue(q.catalogue).objects[4]
    assert any(i.catalogue=='CDS I/311/hip2'and i.identifier=='5'for i in obj.external_ids)
    record['hipparcos2_reference']['epoch']['scale']='changed'
    assert cat.to_record()['hipparcos2_reference']['epoch']['scale']is None
    assert not hasattr(cat.rows[4],'position_m')and not hasattr(cat.rows[4],'velocity_m_s')
    fp.close();gp.close();p.close()


@pytest.mark.parametrize('change',[None,{'radial_velocity':None},{'parallax':None},
    {'parallax':-1.},{'parallax':0.},{'pmra':None},{'astrometric_params_solved':3}])
def test_hip2_fallback_uses_gaia_angular_availability_not_old_inventory_preference(motion_source,change):
    cat,p,q=stellar_hip2_case(motion_source(change,hip2_hips=(1,4,5,7)))
    selected={k.value for k in q.objects}
    use_hip1=change is not None and ('pmra'in change or 'astrometric_params_solved'in change)
    assert selected=={'hipparcos:4','hipparcos:5','hipparcos:7'}|({'hipparcos:1'}if use_hip1 else set())
    assert len(cat.rows)==9
    assert next(cat.source.records())['published_association']is not None
    p.close()


@pytest.mark.parametrize('days',[-18262500,-365.25,0.,365.25,18262500])
def test_hip2_angular_normal_triad_has_independent_astropy_unit_oracle(motion_source,days):
    from astropy import units as u
    from astropy.coordinates import (UnitSphericalRepresentation,UnitSphericalCosLatDifferential,
                                     CartesianRepresentation,CartesianDifferential)
    from math import floor,hypot
    cat,p,q=stellar_hip2_case(motion_source(hip2_change=dict(RArad=.9,DErad=1.,pmRA=1000.,pmDE=-2000.)))
    row=cat.rows[4];epoch=row.source_epoch
    sky=UnitSphericalRepresentation(.9*u.rad,1.*u.rad,
        differentials=UnitSphericalCosLatDifferential(1000*u.mas/u.yr,-2000*u.mas/u.yr))
    cart=sky.represent_as(CartesianRepresentation,CartesianDifferential)
    initial=cart.xyz.value;derivative=cart.differentials['s'].d_xyz.to_value(1/u.s)
    assert max(abs(a-b)for a,b in zip(row.tangent_per_s,derivative))<1e-27
    whole=floor(epoch.jd2+days+.5)
    time=TimePoint(epoch.jd1+whole,epoch.jd2+days-whole,'tcb')
    expected=initial+days*86400*derivative;expected/=hypot(*expected)
    with Kernel(references=(q.reference,))as kernel:
        kernel.register(p,ownership='owned')
        with kernel.open_session(SessionPolicy((q.catalogue,)))as session:
            state=session.evaluate(replace(q,times=(time,))).states[0]
    assert max(abs(a-b)for a,b in zip(state.vector,expected))<2e-15
    assert state.source_epoch==epoch and state.time==time


@pytest.mark.parametrize('changes',[{'pmRA':None},{'DErad':None},{'pmRA':0.,'pmDE':0.},
    {'Plx':None},{'Plx':-1.},{'Sn':0},{'Sn':159,'Nc':2}])
def test_hip2_missing_angular_fields_stay_unavailable_and_unused_fields_do_not_veto(motion_source,changes):
    cat,p,q=stellar_hip2_case(motion_source(hip2_change=changes))
    selected=p.describe().admissions[0].objects
    assert bool(selected)==(not any(k in changes and changes[k]is None for k in ('pmRA','DErad')))
    src=next(cat.source.records('hipparcos2_sources_v1.jsonl'))
    assert all(src[k]==v for k,v in changes.items())
    if not selected:assert cat.rows[4].unavailable_reason.startswith('missing_hipparcos2_')
    p.close()


@pytest.mark.parametrize('fault',['policy','scale','outside','declared_source_scale','cartesian','velocity','warm_scale','foreign_model'])
def test_hip2_policy_and_capability_refusals_after_valid_baseline(motion_source,fault):
    from wenu_kernel.records import TimeSpan
    source=motion_source();cat,p,q=stellar_hip2_case(source);baseline=p.evaluate(q)
    if fault=='policy':
        with pytest.raises(ValueError):bridge.admit_stellar_hipparcos2_motion(source,coverage=cat.coverage,epoch_policy='verified-tcb')
    elif fault=='scale':
        with pytest.raises(ValueError):stellar_hip2_case(source,coverage=TimeSpan(TimePoint(2400000,0,'tt'),TimePoint(2500000,0,'tt')))
    elif fault=='outside':
        with pytest.raises(ValueError):stellar_hip2_case(source,coverage=TimeSpan(TimePoint(2451545,0,'tcb'),TimePoint(2451546,0,'tcb')))
    elif fault=='declared_source_scale':
        with pytest.raises(ValueError):stellar_hip2_case(motion_source(hip2_scale='tt'))
    elif fault=='cartesian':
        with pytest.raises(ValueError):bridge.StellarMotionProvider(cat,representation='cartesian')
    else:
        bad=replace(q,require_velocity=True)if fault=='velocity'else replace(q,times=(TimePoint(2448349,.0625,'tt'),))
        if fault=='foreign_model':
            _,gp,gq=stellar_angular_case(source);bad=replace(q,model=gq.model);gp.close()
        assert not p.supports(bad).supported
        with pytest.raises(UnsupportedCapability):p.evaluate(bad)
    assert p.evaluate(q)==baseline
    p.close()


def test_hip2_reads_source_epoch_and_accepts_pole_zero_pm_without_default_literals(motion_source):
    cat,p,q=stellar_hip2_case(motion_source(hip2_epoch=1992.,hip2_change=dict(RArad=0.,DErad=1.5707963267,pmRA=0.,pmDE=0.)))
    row=cat.rows[4]
    assert row.source_epoch==TimePoint(2448623,0.,'tcb')
    q=replace(q,times=(row.source_epoch,cat.coverage.start,cat.coverage.stop))
    states=p.evaluate(q).states
    assert all(s.vector==states[0].vector for s in states)
    p.close()


if __name__ == '__main__':
    unittest.main()



@pytest.mark.parametrize('kind',['gaia','hipparcos2'])
def test_stellar_long_term_frame_is_explicit_derived_view_with_native_time_and_source_intact(motion_source,monkeypatch,kind):
    from wenu.astrometric_coordinates import LongTermFrame,orient_direction_batch
    from wenu_kernel.records import TimeSpan
    import builtins,socket,erfa
    source=motion_source();before=source.products
    domain=TimeSpan(TimePoint(-16000000,0,'tcb'),TimePoint(21000000,0,'tcb'))
    if kind=='gaia':cat=bridge.admit_stellar_angular_motion(source,coverage=domain)
    else:cat=bridge.admit_stellar_hipparcos2_motion(source,coverage=domain,epoch_policy='nominal-tcb-deferred-qualification')
    native_digest=cat.to_record()['angular_solutions_sha256']
    p=bridge.StellarMotionProvider(cat);a=p.describe().admissions[0]
    q=StateQuery(a.catalogue,a.model,a.objects,(TimePoint(1356174,0,'tcb'),),a.reference,AccuracyRequest())
    with Kernel(references=(a.reference,))as kernel:
        kernel.register(p,ownership='owned')
        with kernel.open_session(SessionPolicy((a.catalogue,)))as session:batch=session.evaluate(q)
    def forbidden(*args,**kwargs):raise AssertionError('frame orientation must not fetch observer/EOP/network resources')
    monkeypatch.setattr(socket,'socket',forbidden)
    original_import=builtins.__import__
    def guarded(name,*args,**kwargs):
        if name.startswith(('astropy','wenu.observer','wenu.coordinate_service','skyfield')):forbidden()
        return original_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    validity=TimeSpan(TimePoint(-70598455,0,'tt'),TimePoint(75501545,0,'tt'))
    first=LongTermFrame(equinox=TimePoint(1356174,0,'tt'),validity=validity,
        axes='mean-equator-equinox',model_policy='vcw2011-2012-erfa')
    second=LongTermFrame(equinox=TimePoint(2451545,0,'tt'),validity=validity,
        axes='mean-ecliptic-equinox',model_policy='vcw2011-2012-erfa')
    x=orient_direction_batch(batch,admission=a,orientation=first)
    y=orient_direction_batch(batch,admission=a,orientation=second)
    assert x.original is y.original is batch and x.orientation.model!=y.orientation.model
    assert x.states[0].vector!=y.states[0].vector
    for n,u,v in zip(batch.states,x.states,y.states):
        assert u.original is v.original is n
        assert n.time==TimePoint(1356174,0,'tcb') and n.reference.frame_id=='icrs'
        assert n.evidence.physical_model.status=='not_evaluated'
    assert cat.source.products==before and cat.to_record()['angular_solutions_sha256']==native_digest
 


# K4b.05: external mathematical reference, not a physical-accuracy oracle.
# Butkevich & Lindegren 2014, A&A 570 A62, Sect. 5.5, Eqs. (83)-(84):
# https://arxiv.org/pdf/1407.4664 (reviewed 2026-10-23).
# This spherical departure/bearing implementation never reads admitted SI rows,
# calls the production engine, or applies a library space-motion routine.
def stellar_no_light_time_reference(source, elapsed_years, *, angular):
    from math import atan2, cos, hypot, sin
    from astropy import units as u
    ra = (source['ra'] * u.deg).to_value(u.rad)
    dec = (source['dec'] * u.deg).to_value(u.rad)
    east = (source['pmra'] * u.mas).to_value(u.rad)
    north = (source['pmdec'] * u.mas).to_value(u.rad)
    speed = hypot(east, north)
    radial_rate = 0.
    if not angular:
        # Independent unit algebra: RV * parallax / au, in reciprocal Julian yr.
        # Spectroscopic RV remains the same nominal proxy used by admission.
        radial_rate = (source['radial_velocity'] * u.km/u.s *
                       source['parallax'] * u.mas/u.au).to_value(
                           1/u.yr, equivalencies=u.dimensionless_angles())
    departure = atan2(speed * elapsed_years, 1 + radial_rate * elapsed_years)
    bearing = atan2(east, north) if speed else 0.
    # Great-circle displacement in the source meridian, then longitude rotation.
    # atan2 handles negative elapsed time and passage beyond a right angle.
    local_x = cos(dec)*cos(departure) - sin(dec)*sin(departure)*cos(bearing)
    local_y = sin(departure)*sin(bearing)
    z = sin(dec)*cos(departure) + cos(dec)*sin(departure)*cos(bearing)
    return (cos(ra)*local_x - sin(ra)*local_y,
            sin(ra)*local_x + cos(ra)*local_y, z)


_NO_LIGHT_TIME_CHORD_TOLERANCE = 5e-14
# Comparison threshold for these conditioned synthetic/cache samples only,
# roughly 0.01 microarcsec. Not a propagated measurement/model/error certificate.
_NO_LIGHT_TIME_CASES = [
    dict(ra=123., dec=-45., parallax=100., pmra=-111., pmdec=23., radial_velocity=44.),
    dict(ra=359.999, dec=12., parallax=200., pmra=4000., pmdec=-2000., radial_velocity=-130.),
    dict(ra=10., dec=90., parallax=30., pmra=1200., pmdec=300., radial_velocity=70.),
    dict(ra=255., dec=-89.999999, parallax=100., pmra=-900., pmdec=1500., radial_velocity=-80.),
    dict(ra=269., dec=4., parallax=550., pmra=-800., pmdec=10300., radial_velocity=-110.),
    dict(ra=211., dec=32., parallax=50., pmra=0., pmdec=0., radial_velocity=60.),
    dict(ra=72., dec=-9., parallax=10., pmra=0., pmdec=0., radial_velocity=0.),
]


@pytest.mark.parametrize('kind', ['full', 'angular', 'hip2'])
@pytest.mark.parametrize('parameters', _NO_LIGHT_TIME_CASES)
def test_stellar_no_light_time_spherical_reference(motion_source, kind, parameters):
    """Protect source-to-query composition; existing affine/PV tests check the core."""
    from fractions import Fraction
    from math import degrees, dist, radians
    from wenu_kernel.records import ObjectKey, TimeSpan
    span = TimeSpan(TimePoint(-2000000, 0, 'tcb'), TimePoint(7000000, 0, 'tcb'))
    if kind == 'hip2':
        # Respect the synthetic fixed-width Hip2 record. Use its actual rounded
        # source coordinates in the oracle; never compare to pre-capture values.
        source = motion_source(hip2_change=dict(RArad=int(radians(parameters['ra'])*1e9)/1e9,
            DErad=int(radians(parameters['dec'])*1e9)/1e9, pmRA=parameters['pmra'],
            pmDE=parameters['pmdec']))
        cat, provider, query = stellar_hip2_case(source, coverage=span)
        native = next(source.records('hipparcos2_sources_v1.jsonl'))
        parameters = dict(parameters, ra=degrees(native['RArad']), dec=degrees(native['DErad']))
        target = '5'
    else:
        source = motion_source(parameters)
        factory = stellar_motion_case if kind == 'full' else stellar_angular_case
        cat, provider, query = factory(source, coverage=span)
        target = '1'
    original = source.products
    record = cat.to_record()
    epoch = next(r.source_epoch for r in cat.rows if r.identifier == target)
    years = (0, -100, 100, -1000, 1000, -10000, 10000)
    times = tuple(TimePoint(epoch.jd1 + int(Fraction(y)*1461//4),
                           epoch.jd2 + float(Fraction(y)*1461/4 % 1), 'tcb')
                  for y in years)
    query = replace(query, objects=(ObjectKey('hipparcos:'+target),), times=times)
    with Kernel(references=(query.reference,)) as kernel:
        kernel.register(provider, ownership='owned')
        with kernel.open_session(SessionPolicy((query.catalogue,))) as session:
            batch = session.evaluate(query)
    assert len(batch.states) == len(years)
    for state, year, time in zip(batch.states, years, times):
        expected = stellar_no_light_time_reference(parameters, year, angular=kind != 'full')
        assert dist(state.vector, expected) <= _NO_LIGHT_TIME_CHORD_TOLERANCE
        assert state.source_epoch == epoch and state.time == state.anchor_time == time
        assert batch.query.model == query.model and state.reference == query.reference
        assert state.evidence.measurement.status == state.evidence.physical_model.status == 'not_evaluated'
    assert source.products == original and cat.to_record() == record
    if kind != 'full':
        assert record['policies']['distance'] == record['policies']['radial_velocity'] == 'not-used'


@pytest.mark.parametrize('fault', ['drop_radial', 'exchange_xy_velocity'])
def test_stellar_no_light_time_reference_detects_motion_fault(motion_source, monkeypatch, fault):
    """A coherent wrong affine engine must fail the independent spherical oracle."""
    from math import dist
    from wenu import astrometric_state as engine
    from wenu_kernel.records import ObjectKey, TimeSpan
    src = _NO_LIGHT_TIME_CASES[1]
    span = TimeSpan(TimePoint(-2000000, 0, 'tcb'), TimePoint(7000000, 0, 'tcb'))
    cat, provider, query = stellar_motion_case(motion_source(src), coverage=span)
    epoch = cat.rows[0].source_epoch
    year = 10000
    query = replace(query, objects=(ObjectKey('hipparcos:1'),),
                    times=(TimePoint(epoch.jd1+3652500, epoch.jd2, 'tcb'),))
    expected = stellar_no_light_time_reference(src, year, angular=False)
    assert dist(provider.evaluate(query).states[0].vector, expected) < _NO_LIGHT_TIME_CHORD_TOLERANCE
    coefficients = engine._motion_coefficients
    def broken(row):
        position, velocity = coefficients(row)
        if row.identifier == '1':
            if fault == 'drop_radial':
                rate = sum(p*v for p,v in zip(position,velocity))/sum(p*p for p in position)
                velocity = tuple(v-rate*p for p,v in zip(position,velocity))
            else:
                velocity = (velocity[1], velocity[0], velocity[2])
        return position, velocity
    monkeypatch.setattr(engine, '_motion_coefficients', broken)
    # Both the engine's affine evaluation and its internal numerical check now
    # see the same wrong coefficients; the external reference must expose it.
    actual = provider.evaluate(query).states[0].vector
    assert dist(actual, expected) > 1e-5
    with pytest.raises(AssertionError):
        assert dist(actual, expected) <= _NO_LIGHT_TIME_CHORD_TOLERANCE
    provider.close()


def stellar_perspective_departure_reference(source, elapsed_years):
    """Signed full-minus-angular departure; source scalars, no engine rows.

    The two directions share one great circle. The atan2 difference identity
    avoids subtracting nearby departures and stays finite beyond 90 degrees.
    Positive is along the source's positive proper-motion bearing. This is a
    matched nominal-model difference, never a physical error certificate.
    """
    from math import atan2, hypot
    from astropy import units as u
    speed = (hypot(source['pmra'], source['pmdec']) * u.mas).to_value(u.rad)
    radial_rate = (source['radial_velocity'] * u.km/u.s *
                   source['parallax'] * u.mas/u.au).to_value(
                       1/u.yr, equivalencies=u.dimensionless_angles())
    tangent = speed * elapsed_years
    radial = radial_rate * elapsed_years
    return atan2(-tangent * radial, 1 + radial + tangent*tangent)


_PERSPECTIVE_CASES = _NO_LIGHT_TIME_CASES + [
    dict(ra=359.999, dec=89.999999, parallax=600., pmra=4000.,
         pmdec=-2000., radial_velocity=-600.),
    dict(ra=12., dec=-90., parallax=600., pmra=-4000.,
         pmdec=2000., radial_velocity=600.),
    dict(ra=211., dec=32., parallax=50., pmra=3000.,
         pmdec=-2000., radial_velocity=0.),
]


@pytest.mark.parametrize('parameters', _PERSPECTIVE_CASES)
def test_stellar_finite_perspective_comparison(motion_source, parameters):
    """Protect comparing a local RV derivative as a finite model difference.

    The closest oracle test above checks each model independently. Here both
    SDK batches must represent the same source/epoch/HIP; their measured
    separation and orientation must match a scalar difference expression.
    """
    from contextlib import ExitStack
    from math import atan2, cos, dist, fsum, hypot, radians, sin
    from wenu_kernel.records import ObjectKey, TimeSpan
    span = TimeSpan(TimePoint(-2000000, 0, 'tcb'), TimePoint(7000000, 0, 'tcb'))
    source = motion_source(parameters)
    original = (source.products, source.manifest)
    full, fp, fq = stellar_motion_case(source, coverage=span)
    angular, ap, aq = stellar_angular_case(source, coverage=span)
    records = (full.to_record(), angular.to_record())
    epoch = full.rows[0].source_epoch
    assert epoch == angular.rows[0].source_epoch
    years = (0, -1000, 1000, -10000, 10000)
    times = tuple(TimePoint(epoch.jd1 + year*1461//4, epoch.jd2, 'tcb')
                  for year in years)
    target = (ObjectKey('hipparcos:1'),)
    fq, aq = (replace(q, objects=target, times=times) for q in (fq, aq))
    assert fq.model != aq.model and fq.reference != aq.reference
    assert fp.catalogue(fq.catalogue).objects[0].external_ids == ap.catalogue(aq.catalogue).objects[0].external_ids
    with ExitStack() as stack:
        batches = []
        for provider, query in ((fp, fq), (ap, aq)):
            kernel = stack.enter_context(Kernel(references=(query.reference,)))
            kernel.register(provider, ownership='owned')
            session = stack.enter_context(kernel.open_session(SessionPolicy((query.catalogue,))))
            batches.append(session.evaluate(query))
    def cross(a, b):
        return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    ra, dec = radians(parameters['ra']), radians(parameters['dec'])
    east = (-sin(ra), cos(ra), 0.)
    north = (-sin(dec)*cos(ra), -sin(dec)*sin(ra), cos(dec))
    speed = hypot(parameters['pmra'], parameters['pmdec'])
    tangent = tuple((parameters['pmra']*a + parameters['pmdec']*d)/speed
                    for a, d in zip(east, north)) if speed else east
    origin = (cos(dec)*cos(ra), cos(dec)*sin(ra), sin(dec))
    normal = cross(origin, tangent)
    for fs, angular_state, year, time in zip(*[b.states for b in batches], years, times, strict=True):
        assert fs.object_key == angular_state.object_key == target[0]
        for state, query in ((fs, fq), (angular_state, aq)):
            assert state.source_epoch == epoch and state.time == state.anchor_time == time
            assert state.reference == query.reference
            assert state.evidence.measurement.status == state.evidence.physical_model.status == 'not_evaluated'
        fv, av = fs.vector, angular_state.vector
        dot = fsum(a*b for a, b in zip(fv, av))
        separation = atan2(hypot(*cross(av, fv)), dot)
        signed = atan2(fsum(a*b for a, b in zip(cross(av, fv), normal)), dot)
        expected = stellar_perspective_departure_reference(parameters, year)
        assert abs(separation - abs(expected)) <= _NO_LIGHT_TIME_CHORD_TOLERANCE
        assert abs(signed - expected) <= _NO_LIGHT_TIME_CHORD_TOLERANCE
        # Reuse the accepted separate spherical expression as a second check;
        # it does not read SI rows or share the scalar difference identity.
        for vector, angular_model in ((fv, False), (av, True)):
            assert dist(vector, stellar_no_light_time_reference(parameters, year,
                        angular=angular_model)) <= _NO_LIGHT_TIME_CHORD_TOLERANCE
        if not year or not speed or not parameters['radial_velocity']:
            assert separation <= _NO_LIGHT_TIME_CHORD_TOLERANCE
        else:
            assert signed * parameters['radial_velocity'] < 0
        if abs(parameters['radial_velocity']) == 600 and abs(year) == 10000:
            # These constructed cases pass the full trajectory's 90-degree
            # departure on one time side. A local derivative cannot replace it.
            assert separation > .1
    assert (source.products, source.manifest) == original
    assert (full.to_record(), angular.to_record()) == records


def test_stellar_perspective_pair_preserves_gaps_and_domain_refusal(motion_source):
    """A successful pair must not authorize full states for angular-only HIPs."""
    from contextlib import ExitStack
    from wenu_kernel.errors import OutsideCoverage
    from wenu_kernel.records import ObjectKey
    source = motion_source()
    full, fp, fq = stellar_motion_case(source)
    angular, ap, aq = stellar_angular_case(source, coverage=full.coverage)
    assert len(full.rows) == len(angular.rows) == 9
    common = tuple(key for key in fq.objects if key in aq.objects)
    assert common == (ObjectKey('hipparcos:1'), ObjectKey('hipparcos:6'))
    assert full.rows[1].unavailable_reason == 'missing_gaia_radial_velocity'
    assert angular.rows[1].unavailable_reason is None
    with ExitStack() as stack:
        for provider, query in ((fp, fq), (ap, aq)):
            kernel = stack.enter_context(Kernel(references=(query.reference,)))
            kernel.register(provider, ownership='owned')
            session = stack.enter_context(kernel.open_session(SessionPolicy((query.catalogue,))))
            paired = replace(query, objects=common)
            baseline = session.evaluate(paired)
            gap = replace(query, objects=(ObjectKey('hipparcos:2'),))
            if provider is fp:
                with pytest.raises(UnsupportedCapability):
                    session.evaluate(gap)
            else:
                assert session.evaluate(gap).states[0].object_key == gap.objects[0]
            outside = replace(paired, times=(TimePoint(full.coverage.stop.jd1+1, 0, 'tcb'),))
            with pytest.raises(OutsideCoverage):
                session.evaluate(outside)
            assert session.evaluate(paired) == baseline


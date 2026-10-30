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
              hip2_change=None, hip2_hips=(5,), hip2_epoch=1991.25, hip2_scale=None,
              extra_photometry=None):
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
            original=dict(hip=hip,magnitude=original_v if i==1 else (extra_photometry or {}).get(i), designation={'names':['Synthetic star']})
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


def _production_stars(source):
    """Constructed full source with original V and deliberately different axes."""
    import numpy as np
    from wenu.objects.stars import Stars
    records = list(source.records())
    table = pd.DataFrame(dict(magnitude=[r['original']['magnitude'] for r in records],
        ra_degrees=[83.] * len(records), ra_hours=[83./15] * len(records),
        dec_degrees=[0.] * len(records), epoch_year=[1991.25] * len(records)),
        index=[int(r['identity']['identifier']) for r in records])
    metadata = dict(source.metadata['original_metadata'], schema='wenu-stellar-catalogue/1',
        provenance=['Constructed integration source'], source_metadata={})
    metadata['units'] = dict(metadata['units'], ra_degrees='deg', dec_degrees='deg',
                             ra_hours='hourangle', epoch_year='Julian year')
    stars = Stars(None)
    stars.source_catalog = ingest_stellar_catalogue(table, StellarCatalogueMetadata.from_record(metadata)).table
    stars.catalog = stars.source_catalog.iloc[:1].copy()
    return stars


def _production_motion(source, instant=TimePoint(2457389, 0., 'tcb')):
    from wenu_kernel.records import TimeSpan
    domain = TimeSpan(TimePoint(-2000000, 0., 'tcb'), TimePoint(3000000, 0., 'tcb'))
    return bridge.StellarMotionRequest((
        bridge.admit_stellar_motion(source, coverage=domain,
            distance_policy='positive-parallax-reciprocal', radial_velocity_policy='spectroscopic-proxy'),
        bridge.admit_stellar_angular_motion(source, coverage=domain),
        bridge.admit_stellar_hipparcos2_motion(source, coverage=domain,
            epoch_policy='nominal-tcb-deferred-qualification')),
        instant)


def test_stellar_realized_view_identity_gaps_reuse_and_isolation(motion_source):
    """Protect the production seam against static bypass and source mutation."""
    import numpy as np
    source = motion_source()
    stars = _production_stars(source)
    before = stars.native_positions()
    request = _production_motion(source)
    with stars.realized(request) as first:
        with pytest.raises(ValueError, match='native ICRS only'):
            first.observed_altaz()
        with pytest.raises(ValueError, match='native ICRS only'):
            first.spherical_geometry(None)
        assert len(first.native_positions(()).ids) == 0
        assert first._stellar_realization.report()['sdk_batches_evaluated'] == 0
        positions = first.native_positions((8, 1, 4, 2, 5))
        assert list(positions.ids) == [1, 2, 4, 5, 8]
        assert list(positions.metadata['stellar_motion_status']) == ['evaluated', 'evaluated', 'unavailable', 'evaluated', 'evaluated']
        assert np.isnan(positions.lon_deg[2])
        assert positions.lon_deg[0] != before.lon_deg[0]
        assert positions.metadata['magnitude'][0] == 2.
        assert positions.coordinate_spec.time_scale == 'tcb'
        np.testing.assert_array_equal(first.position().lon_deg, first.native_positions((1,)).lon_deg)
        assert first._stellar_realization.report()['exact_batch_reuses'] > 0
        with stars.realized(replace(request, instant=TimePoint(2467389, 0., 'tcb'))) as second:
            assert second.native_positions((1,)).lon_deg[0] != positions.lon_deg[0]
            np.testing.assert_array_equal(first.native_positions((1,)).lon_deg, positions.lon_deg[:1])
        np.testing.assert_array_equal(stars.native_positions().lon_deg, before.lon_deg)
    with pytest.raises(ClosedSession):
        first.native_positions((1,))
    assert not hasattr(stars, '_stellar_realization')


def test_stellar_realization_dependents_are_position_consumers(motion_source, tmp_path):
    """Lines/labels receive no motion options; source groups survive migration."""
    import numpy as np
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.constellation_labels import ConstellationLabels
    from wenu.sky.assembly import stellar_realization_sky
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    sky = CelestialSphere(None)
    sky.stars = _production_stars(motion_source())
    path = tmp_path / 'synthetic.fab'
    path.write_text('Ori 3 1 2 5 4\n')
    sky.constellation_lines = ConstellationLines(sky.stars, filename=path)
    sky.constellation_labels = ConstellationLabels(sky.stars, min_stars=1)
    from types import SimpleNamespace
    sky.constellations = SimpleNamespace(stars=sky.stars, lines=sky.constellation_lines)
    sky.extend((sky.stars, sky.constellation_lines, sky.constellation_labels))
    with stellar_realization_sky(sky, _production_motion(motion_source())) as view:
        assert view.stars is not sky.stars
        assert view.constellation_lines.stars is view.constellation_labels.stars is view.stars
        assert view.constellations.stars is view.stars
        assert view.constellations.lines is view.constellation_lines
        context = LayerRealizationContext(NATIVE_ICRS_SPEC)
        points = view.stars.native_positions()
        from wenu.sky.constellation_lines import UnresolvedConstellationStarWarning
        with pytest.warns(UnresolvedConstellationStarWarning, match='4'):
            curves = view.constellation_lines.realize(context, None)
        anchors = view.constellation_labels.realize(context, None)
        assert list(anchors.labels) == ['Ori']  # moved directions are not Orion
        assert len(curves.lon_deg) == 2  # third edge has unavailable endpoint
        np.testing.assert_allclose(np.column_stack((curves.lon_deg[0], curves.lat_deg[0])),
                                   np.column_stack((points.lon_deg, points.lat_deg))[:2])
        assert anchors.coordinate_spec == points.coordinate_spec
        assert not hasattr(view.constellation_lines, '_stellar_realization')
        assert not hasattr(view.constellation_labels, '_stellar_realization')
    assert sky.constellation_lines.stars is sky.constellation_labels.stars is sky.stars
    assert tuple(sky.layers) == (sky.stars, sky.constellation_lines, sky.constellation_labels)


def test_stellar_realization_refuses_binding_domain_transport_and_warm_failure(motion_source, monkeypatch):
    import pickle
    from wenu_kernel import KernelSession
    source = motion_source()
    stars = _production_stars(source)
    request = _production_motion(source)
    with pytest.raises(TypeError, match='transport'):
        pickle.dumps(request)
    with pytest.raises(ValueError, match='domain'):
        replace(request, instant=TimePoint(4000000, 0., 'tcb'))
    wrong = stars.source_catalog.copy(deep=True)
    wrong.loc[1, 'magnitude'] = 3.
    stars.source_catalog = wrong
    with pytest.raises(ValueError, match='photometry'):
        with stars.realized(request):
            pytest.fail('wrong source must refuse')
    stars = _production_stars(source)
    with stars.realized(request) as view:
        view.native_positions((1,))
        def refuse(*args):
            raise UnsupportedCapability('synthetic warm SDK refusal')
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
        with pytest.raises(UnsupportedCapability, match='warm SDK refusal'):
            view.native_positions((1,))


def test_stellar_native_sheet_binds_view_and_closes_on_render_failure(motion_source, monkeypatch):
    """Public sheet entry owns cleanup; no mutation of a supplied sky."""
    from wenu.charts import atlas_sheet
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu_kernel.errors import ClosedSession
    sky = CelestialSphere(None)
    sky.stars = _production_stars(motion_source())
    sky.add(sky.stars)
    # Validation of sheet/page geometry has its existing independent owner.
    request = object.__new__(atlas_sheet.AtlasSheetChartRequest)
    object.__setattr__(request, 'stellar_motion', _production_motion(motion_source()))
    seen = []
    def render(request, bound):
        seen.append(bound.stars)
        assert bound.stars is not sky.stars
        assert bound.stars.native_positions((1,)).coordinate_spec.time_scale == 'tcb'
        raise RuntimeError('synthetic renderer failure')
    monkeypatch.setattr(atlas_sheet, '_render_atlas_sheet', render)
    with pytest.raises(RuntimeError, match='renderer failure'):
        atlas_sheet.render_atlas_sheet(request, sky)
    with pytest.raises(ClosedSession):
        seen[0].native_positions((1,))
    assert not hasattr(sky.stars, '_stellar_realization')


@pytest.mark.integration
def test_stellar_motion_public_native_sheet_export(motion_source, tmp_path):
    """Constructed stellar data through real preparation/render/report/export."""
    from wenu.atlas_design import AtlasSheetGeometry, AtlasPageGeometry
    from wenu.charts.atlas_sheet import AtlasSheetChartRequest, AtlasChartPresentation
    from wenu.charts.request_generation import generate_chart_request
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.constellation_labels import ConstellationLabels
    sky = CelestialSphere(None)
    sky.stars = _production_stars(motion_source())
    path = tmp_path / 'synthetic-export.fab'
    path.write_text('Ori 1 1 2\n')
    sky.constellation_lines = ConstellationLines(sky.stars, filename=path)
    sky.constellation_labels = ConstellationLabels(sky.stars, min_stars=1)
    sky.extend((sky.stars, sky.constellation_lines, sky.constellation_labels))
    request = AtlasSheetChartRequest(
        AtlasSheetGeometry('synthetic', 1, 0., 0., 40.),
        AtlasPageGeometry(250., 353., 10., 10., 10., 10.),
        AtlasChartPresentation(layers=('stars', 'constellation_lines', 'constellation_labels'),
                               formats=('png', 'pdf', 'svg'), dpi=36,
                               report_label_scale=1., legend_fontsize=6.),
        tmp_path / 'sheet', stellar_motion=_production_motion(motion_source()))
    result = generate_chart_request(request, sky=sky)
    assert len(result.outputs) == 7
    assert all(path.is_file() and path.stat().st_size > 0 for path in result.outputs)
    report = json.loads((request.output_dir / 'chart-01_report_data.json').read_text())
    assert report['stellar_realization']['epoch']['scale'] == 'tcb'
    assert report['stellar_realization']['model_counts']['unavailable'] == 3
    assert report['stellar_realization']['physical_accuracy'] == 'unknown'
    assert not hasattr(sky.stars, '_stellar_realization')


@pytest.mark.parametrize('failure', ['register', 'open_session', 'evaluate'])
def test_stellar_realization_closes_partial_resources(motion_source, monkeypatch, failure):
    """Provider ownership survives partial admission and first-query refusal."""
    from wenu_kernel import KernelSession
    created = []
    factory = bridge.StellarMotionProvider
    def capture(*args, **kwargs):
        provider = factory(*args, **kwargs)
        created.append(provider)
        return provider
    monkeypatch.setattr(bridge, 'StellarMotionProvider', capture)
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic partial resource failure')
    monkeypatch.setattr(KernelSession if failure == 'evaluate' else Kernel, failure, refuse)
    stars = _production_stars(motion_source())
    with pytest.raises(RuntimeError, match='partial resource failure'):
        with stars.realized(_production_motion(motion_source())) as view:
            view.native_positions()
    assert created
    for provider in created:
        with pytest.raises(ClosedSession):
            provider.describe()
    assert not hasattr(stars, '_stellar_realization')


def test_stellar_realization_restored_facade_keeps_explicit_binding(motion_source):
    """Restored source facade may bind motion; it does not infer one."""
    import numpy as np
    from wenu.sky.assembly import _SnapshotStars
    source = motion_source()
    cold = _production_stars(source)
    restored = _SnapshotStars(None)
    restored.source_catalog = cold.source_catalog.copy(deep=True)
    restored.catalog = cold.catalog.copy(deep=True)
    before = restored.native_positions()
    with restored.realized(_production_motion(source)) as view:
        assert type(view) is _SnapshotStars
        assert view.native_positions((1,)).lon_deg[0] != before.lon_deg[0]
    np.testing.assert_array_equal(restored.native_positions().lon_deg, before.lon_deg)


@pytest.fixture
def motion_document(motion_source, tmp_path, request):
    """Byte-bound synthetic local source and explicit motion TOML."""
    from hashlib import sha256
    source = motion_source(**getattr(request, 'param', {}))
    directory = tmp_path / 'synthetic-source'
    directory.mkdir()
    for name, raw in source.products:
        (directory / name).write_bytes(raw)
    (directory / 'source_manifest_v1.json').write_bytes(source.manifest)
    models = [
        dict(motion_policy='full-input-rectilinear',
             distance_policy='positive-parallax-reciprocal',
             radial_velocity_policy='spectroscopic-proxy'),
        dict(motion_policy='proper-motion-angular',
             distance_policy='not-used', radial_velocity_policy='not-used'),
        dict(motion_policy='hipparcos2-angular-fallback',
             distance_policy='not-used', radial_velocity_policy='not-used',
             epoch_policy='nominal-tcb-deferred-qualification')]
    for model in models:
        model.update(start_jyear_tcb=-8001., stop_jyear_tcb=2050.)
    data = dict(schema_version=1, document_kind='wenu-stellar-motion-request',
                source_directory='synthetic-source',
                source_manifest_sha256=sha256(source.manifest).hexdigest(),
                target_jyear_tcb=2000., models=models)
    def write(change=None):
        from copy import deepcopy
        values = deepcopy(data)
        if change:
            change(values)
        def literal(value):
            if type(value) is float:
                return repr(value)
            return json.dumps(value)
        text = '\n'.join(f'{key} = {literal(value)}' for key, value in values.items()
                         if key != 'models') + '\n'
        if type(values.get('models')) is list:
            for model in values['models']:
                text += '\n[[models]]\n' + '\n'.join(
                    f'{key} = {literal(value)}' for key, value in model.items()) + '\n'
        elif 'models' in values:
            text += 'models = ' + literal(values['models']) + '\n'
        path = tmp_path / 'motion-v1.toml'
        path.write_text(text)
        return path
    return source, directory, write


@pytest.mark.parametrize('epoch', [2000., -8000.])
def test_stellar_motion_document_matches_explicit_models(motion_document, monkeypatch, epoch):
    """Protected fault: config must select the same public stellar results."""
    import numpy as np
    from hashlib import sha256
    source, directory, write = motion_document
    path = write(lambda d: d.update(target_jyear_tcb=epoch))
    monkeypatch.chdir(path.parent.parent)  # source paths are document-relative
    request = bridge.load_stellar_motion_request(path)
    expected = _production_motion(source, bridge._stellar_epoch(epoch, 'tcb'))
    assert request.input_document_sha256 == sha256(path.read_bytes()).hexdigest()
    assert request.instant == expected.instant
    assert [c.motion_policy for c in request.catalogues] == [
        c.motion_policy for c in expected.catalogues]
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    stars = _production_stars(source)
    with stars.realized(request) as actual, stars.realized(expected) as reference:
        a, b = actual.native_positions(), reference.native_positions()
        np.testing.assert_array_equal(a.lon_deg, b.lon_deg)
        np.testing.assert_array_equal(a.lat_deg, b.lat_deg)
        assert actual._stellar_realization.report()['input_document_sha256'] == request.input_document_sha256
        assert 'input_document_sha256' not in reference._stellar_realization.report()
    assert {p.name: p.read_bytes() for p in directory.iterdir()} == before


@pytest.mark.parametrize('fault', [
    'schema', 'kind', 'unknown', 'missing', 'digest', 'source', 'boolean-epoch',
    'nan-epoch', 'inf-epoch', 'string-epoch', 'empty-models', 'model-type',
    'model-name', 'duplicate-model', 'missing-policy', 'extra-policy',
    'wrong-distance', 'wrong-rv', 'hip2-epoch', 'nan-domain', 'reverse-domain',
    'uncovered', 'duplicate-key', 'malformed'])
def test_stellar_motion_document_refuses_before_source_loading(motion_document, monkeypatch, fault):
    """Closest existing admission refusals; bad configuration cannot acquire inputs."""
    source, directory, write = motion_document
    def change(d):
        if fault == 'schema': d['schema_version'] = True
        elif fault == 'kind': d['document_kind'] = 'other'
        elif fault == 'unknown': d['observer'] = 'now'
        elif fault == 'missing': del d['source_manifest_sha256']
        elif fault == 'digest': d['source_manifest_sha256'] = 'BAD'
        elif fault == 'source': d['source_directory'] = ''
        elif fault == 'boolean-epoch': d['target_jyear_tcb'] = True
        elif fault == 'nan-epoch': d['target_jyear_tcb'] = float('nan')
        elif fault == 'inf-epoch': d['target_jyear_tcb'] = float('inf')
        elif fault == 'string-epoch': d['target_jyear_tcb'] = '2000'
        elif fault == 'empty-models': d['models'] = []
        elif fault == 'model-type': d['models'] = 'full'
        elif fault == 'model-name': d['models'][0]['motion_policy'] = 'best'
        elif fault == 'duplicate-model': d['models'].append(d['models'][0].copy())
        elif fault == 'missing-policy': del d['models'][0]['distance_policy']
        elif fault == 'extra-policy': d['models'][1]['epoch_policy'] = 'inferred'
        elif fault == 'wrong-distance': d['models'][0]['distance_policy'] = 'prior'
        elif fault == 'wrong-rv': d['models'][0]['radial_velocity_policy'] = 'zero'
        elif fault == 'hip2-epoch': d['models'][2]['epoch_policy'] = 'inferred'
        elif fault == 'nan-domain': d['models'][0]['start_jyear_tcb'] = float('nan')
        elif fault == 'reverse-domain': d['models'][0]['stop_jyear_tcb'] = -9000.
        elif fault == 'uncovered': d['target_jyear_tcb'] = 2051.
    path = write(change)
    if fault == 'empty-models':
        path.write_text(path.read_text() + 'models = []\n')
    if fault == 'duplicate-key':
        path.write_text(path.read_text().replace('schema_version = 1', 'schema_version = 1\nschema_version = 1'))
    if fault == 'malformed':
        path.write_text('broken = [')
    from wenu import stellar_enrichment
    def forbidden(*args, **kwargs):
        raise AssertionError('invalid document reached source loading')
    monkeypatch.setattr(stellar_enrichment, 'load_stellar_enrichment', forbidden)
    with pytest.raises(ValueError):
        bridge.load_stellar_motion_request(path)


@pytest.mark.parametrize('fault', ['manifest', 'payload', 'missing'])
def test_stellar_motion_document_source_integrity(motion_document, fault):
    source, directory, write = motion_document
    path = write()
    if fault == 'manifest':
        path = write(lambda d: d.update(source_manifest_sha256='0' * 64))
    elif fault == 'payload':
        (directory / 'gaia_sources_v1.jsonl').write_bytes(b'{}\n')
    else:
        (directory / 'metadata_v1.json').unlink()
    with pytest.raises((ValueError, OSError)):
        bridge.load_stellar_motion_request(path)


def _motion_cli_sky(source, directory):
    """Constructed sky for the file-adapter seam; no real sky snapshot claim."""
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.constellation_labels import ConstellationLabels
    sky = CelestialSphere(None)
    sky.stars = _production_stars(source)
    path = directory / 'synthetic-lines.fab'
    path.write_text('Ori 1 1 2\n')
    sky.constellation_lines = ConstellationLines(sky.stars, filename=path)
    sky.constellation_labels = ConstellationLabels(sky.stars, min_stars=1)
    sky.extend((sky.stars, sky.constellation_lines, sky.constellation_labels))
    return sky


@pytest.mark.parametrize('fault', ['none', 'static', 'source-sky', 'sdk', 'warm-sdk',
                                  'bad-config', 'manifest', 'existing-output'])
def test_stellar_motion_document_cli_route_and_cleanup(motion_document, monkeypatch, fault):
    """Real command/executor/render seam; synthetic saved-sky reader is explicit."""
    import numpy as np
    from pathlib import Path
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_sheet import AtlasSheetChartRequest, AtlasChartPresentation
    from wenu.charts.request_generation import generate_chart_request
    from wenu.cli.chart import main
    from wenu.sky import native_snapshot
    source, directory, write = motion_document
    config = write()
    root = config.parent
    atlas_path = Path(__file__).parents[1] / 'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json'
    atlas = AtlasBandTiling.from_json(atlas_path.read_text())
    # Select an equatorial sheet near the synthetic source's original axes.
    sheet = min(atlas.geometry.sheets, key=lambda s: abs(s.center_dec_deg) + abs(s.center_ra_deg - 83.))
    style = root / 'style-v1.toml'
    style.write_text('schema_version = 1\ndocument_kind = "wenu-atlas-chart-presentation"\n'
        'layers = ["stars", "constellation_lines", "constellation_labels"]\n'
        'formats = ["png", "pdf", "svg"]\ndpi = 36\nlegend_fontsize = 6.0\nreport_label_scale = 1.0\n')
    sky = _motion_cli_sky(source, root)
    requires = []
    class SyntheticSnapshot:
        def require(self, **kwargs): requires.append(kwargs)
        def make_sky(self): return sky
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot', lambda *a, **k: SyntheticSnapshot())
    out = root / 'cli'
    argv = ['atlas-sheet', '--design', str(atlas_path), '--config', str(style),
        '--from-sky', str(root / 'synthetic-snapshot'), '--chart-number', str(sheet.number),
        '--output-dir', str(out), '--stellar-motion-config', str(config)]
    if fault == 'static':
        argv = argv[:-2]
    elif fault == 'bad-config':
        config.write_text('broken = [')
    elif fault == 'manifest':
        write(lambda d: d.update(source_manifest_sha256='0' * 64))
    if fault == 'source-sky':
        metadata = dict(stellar_table_metadata(sky.stars.source_catalog).to_record())
        metadata['source_sha256'] = 'b' * 64
        sky.stars.source_catalog = ingest_stellar_catalogue(
            sky.stars.source_catalog, StellarCatalogueMetadata.from_record(metadata)).table
    if fault in ('sdk', 'warm-sdk'):
        from wenu_kernel import KernelSession
        original = KernelSession.evaluate
        count = [0]
        def refuse(self, query):
            count[0] += 1
            if fault == 'sdk' or count[0] > 3:
                raise UnsupportedCapability('synthetic SDK refusal')
            return original(self, query)
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    sentinel = None
    if fault == 'existing-output':
        out.mkdir()
        sentinel = out / f'chart-{sheet.number:02d}.png'
        sentinel.write_bytes(b'existing product')
    status = main(argv, emit_outputs=False)
    assert requires and requires[0]['layers'] == ('stars', 'constellation_lines', 'constellation_labels')
    if fault not in ('none', 'static'):
        assert status != 0
        assert (not out.exists()) if sentinel is None else sentinel.read_bytes() == b'existing product'
        assert not list(root.glob('.wenu-chart-*'))
        assert not hasattr(sky.stars, '_stellar_realization')
        return
    assert status == 0
    report = json.loads((out / f'chart-{sheet.number:02d}_report_data.json').read_text())
    if fault == 'static':
        assert 'stellar_realization' not in report
    else:
        assert report['stellar_realization']['input_document_sha256'] == bridge.load_stellar_motion_request(config).input_document_sha256
    expected = root / 'python'
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    presentation = AtlasChartPresentation.from_dict(tomllib.loads(style.read_text()))
    request = AtlasSheetChartRequest(sheet, atlas.geometry.page, presentation, expected,
        stellar_motion=None if fault == 'static' else bridge.load_stellar_motion_request(config))
    generate_chart_request(request, sky=sky)
    assert report == json.loads((expected / f'chart-{sheet.number:02d}_report_data.json').read_text())
    assert (out / f'chart-{sheet.number:02d}.png').read_bytes() == (expected / f'chart-{sheet.number:02d}.png').read_bytes()
    assert len(list(out.iterdir())) == 7


@pytest.mark.parametrize('epoch', [2000., -8000.])
def test_stellar_motion_document_cli_fresh_process(motion_document, epoch):
    """Offline process composition with an explicitly synthetic snapshot seam."""
    from pathlib import Path
    import os, subprocess, sys
    source, directory, write = motion_document
    config = write(lambda d: d.update(target_jyear_tcb=epoch))
    root = config.parent
    script = r'''
from pathlib import Path
import json, socket, sys
from test_stellar_state import motion_source, _motion_cli_sky
from wenu import stellar_state as bridge
from wenu.atlas_design import AtlasBandTiling
from wenu.charts.atlas_sheet import AtlasSheetChartRequest, AtlasChartPresentation
from wenu.charts.request_generation import generate_chart_request
from wenu.cli import chart
from wenu.sky import native_snapshot
def forbidden(*a, **k):
    raise AssertionError('network/observer forbidden in native motion command')
socket.socket.connect = forbidden
chart.Observer = forbidden
root, design = map(Path, sys.argv[1:])
source = motion_source.__wrapped__()()
sky = _motion_cli_sky(source, root)
class SyntheticSnapshot:
    def require(self, **kwargs):
        assert kwargs['layers'] == ('stars', 'constellation_lines', 'constellation_labels')
    def make_sky(self):
        return sky
native_snapshot.read_native_sky_snapshot = lambda *a, **k: SyntheticSnapshot()
atlas = AtlasBandTiling.from_json(design.read_text())
sheet = min(atlas.geometry.sheets, key=lambda s: abs(s.center_dec_deg) + abs(s.center_ra_deg))
style = root / 'style-v1.toml'
style.write_text('schema_version = 1\ndocument_kind = "wenu-atlas-chart-presentation"\n'
    'layers = ["stars", "constellation_lines", "constellation_labels"]\n'
    'formats = ["png", "pdf", "svg"]\ndpi = 36\nlegend_fontsize = 6.0\nreport_label_scale = 1.0\n')
status = chart.main(['atlas-sheet', '--design', str(design), '--config', str(style),
    '--from-sky', str(root / 'synthetic-snapshot'), '--chart-number', str(sheet.number),
    '--output-dir', str(root / 'cli'), '--stellar-motion-config', str(root / 'motion-v1.toml')],
    emit_outputs=False)
assert status == 0
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
presentation = AtlasChartPresentation.from_dict(tomllib.loads(style.read_text()))
motion = bridge.load_stellar_motion_request(root / 'motion-v1.toml')
request = AtlasSheetChartRequest(sheet, atlas.geometry.page, presentation, root / 'python',
                                stellar_motion=motion)
generate_chart_request(request, sky=sky)
stem = f'chart-{sheet.number:02d}'
a = json.loads((root / 'cli' / (stem + '_report_data.json')).read_text())
b = json.loads((root / 'python' / (stem + '_report_data.json')).read_text())
assert a == b
assert a['stellar_realization']['input_document_sha256'] == motion.input_document_sha256
assert a['stellar_realization']['model_counts']['unavailable'] == 3
assert (root / 'cli' / (stem + '.png')).read_bytes() == (root / 'python' / (stem + '.png')).read_bytes()
assert len(list((root / 'cli').iterdir())) == 7
print('PASS: synthetic offline fresh-process command/Python parity')
'''
    repository = Path(__file__).resolve().parents[1]
    design = repository / 'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json'
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        (str(repository / 'src'), str(repository / 'packages/wenu_kernel/src'),
         str(repository / 'tests'))))
    result = subprocess.run([sys.executable, '-c', script, str(root), str(design)],
                            env=env, cwd=root, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'PASS: synthetic offline' in result.stdout


def test_stellar_motion_document_cannot_override_prepared_request(motion_document):
    from wenu.cli.chart import main
    from wenu.atlas_design import AtlasSheetGeometry, AtlasPageGeometry
    from wenu.charts.atlas_sheet import AtlasSheetChartRequest, AtlasChartPresentation
    source, directory, write = motion_document
    config = write()
    request = AtlasSheetChartRequest(AtlasSheetGeometry('synthetic', 1, 0., 0., 40.),
        AtlasPageGeometry(250., 353., 10., 10., 10., 10.),
        AtlasChartPresentation(), config.parent / 'out')
    assert main(['atlas-sheet', '--chart-number', '1', '--output-dir', str(request.output_dir),
                 '--stellar-motion-config', str(config)],
                atlas_request=request, sky=object(), emit_outputs=False) == 2
    assert not request.output_dir.exists()


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
    span = TimeSpan(TimePoint(-2000000, 0, 'tcb'), TimePoint(170000000, 0, 'tcb'))
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
    years = (0, -100, 100, -1000, 1000, -10000, 10000,
             60000, 100000, 450000)
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



@pytest.mark.parametrize('fault', ['none', 'document', 'directory', 'snapshot', 'design', 'model', 'source'])
def test_stellar_execution_input_pins_bytes_paths_and_bindings(motion_document, monkeypatch, fault):
    """Captured configuration survives path edits; corruption never selects defaults."""
    import pickle
    from dataclasses import replace
    source, directory, write = motion_document
    path = write()
    captured, motion = bridge.StellarMotionExecutionInput.capture(path,
        snapshot_sha256='a'*64, design_sha256='b'*64)
    captured = pickle.loads(pickle.dumps(captured))
    assert captured.source_directory == str(directory.resolve())
    path.write_text('invalid = "changed after capture"')
    monkeypatch.chdir(directory)
    if fault == 'document': captured = replace(captured, document=b'changed')
    elif fault == 'directory': captured = replace(captured, source_directory=str(directory.parent))
    elif fault == 'snapshot': captured = replace(captured, snapshot_sha256='c'*64)
    elif fault == 'design': captured = replace(captured, design_sha256='c'*64)
    elif fault == 'model': captured = replace(captured, motion_identity_sha256='c'*64)
    elif fault == 'source':
        payload = directory / source.products[0][0]
        payload.write_bytes(payload.read_bytes()+b' ')
    if fault != 'none':
        with pytest.raises(ValueError):
            captured.admit(snapshot_sha256='a'*64, design_sha256='b'*64)
    else:
        admitted = captured.admit(snapshot_sha256='a'*64, design_sha256='b'*64)
        assert bridge.stellar_motion_identity(admitted) == bridge.stellar_motion_identity(motion)
        with pytest.raises(TypeError): pickle.dumps(admitted)


def test_stellar_sheet_borrows_matching_live_view_without_rebinding(motion_source, monkeypatch, tmp_path):
    from wenu.sky.assembly import stellar_realization_sky
    from wenu.charts import atlas_sheet
    from wenu.atlas_design import AtlasBandTiling
    from pathlib import Path
    source = motion_source()
    sky = _motion_cli_sky(source, tmp_path)
    motion = _production_motion(source)
    atlas = AtlasBandTiling.from_json((Path(__file__).resolve().parents[1] /
        'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json').read_text())
    def consume(request, borrowed):
        return borrowed.stars.native_positions()
    monkeypatch.setattr(atlas_sheet, '_render_atlas_sheet', consume)
    with stellar_realization_sky(sky, motion) as view:
        for sheet in atlas.geometry.sheets[:2]:
            request = atlas_sheet.AtlasSheetChartRequest(sheet, atlas.geometry.page,
                atlas_sheet.AtlasChartPresentation(), tmp_path, stellar_motion=motion)
            atlas_sheet.render_atlas_sheet(request, view)
        assert view.stars._stellar_realization.report()['exact_batch_reuses'] > 0
        with pytest.raises(ValueError, match='differs'):
            atlas_sheet.render_atlas_sheet(replace(request, stellar_motion=None), view)
        with pytest.raises(ValueError, match='differs'):
            atlas_sheet.render_atlas_sheet(replace(request,
                stellar_motion=replace(motion, instant=TimePoint(2467389,0.,'tcb'))), view)
    with pytest.raises(ClosedSession): view.stars.native_positions()
    assert not hasattr(sky.stars, '_stellar_realization')


def _synthetic_publication_worker(directory, digest, command, motion_input, design_sha256, frame_input=None):
    """Spawn seam replaces source-sky decoding only; all stellar code is real."""
    from pathlib import Path
    from wenu.charts import atlas_publication as publication
    from wenu.sky import native_snapshot
    motion = motion_input.admit(snapshot_sha256=digest, design_sha256=design_sha256)
    from os import getpid
    local = Path(directory) / f'worker-{getpid()}'
    local.mkdir()
    source = motion.catalogues[0].source if type(motion) is bridge.StellarMotionRequest else motion.catalogue.source
    sky = _motion_cli_sky(source, local)
    class SyntheticSnapshot:
        manifest_sha256 = digest
        def require(self, **kwargs):
            assert kwargs['design_sha256'] == design_sha256
        def make_sky(self): return sky
    original = native_snapshot.read_native_sky_snapshot
    native_snapshot.read_native_sky_snapshot = lambda *a, **k: SyntheticSnapshot()
    try:
        publication._initialize_atlas_worker(directory, digest, command, motion_input, design_sha256, frame_input)
    finally:
        native_snapshot.read_native_sky_snapshot = original
    # Receipt is written by normal production multiprocessing finalization.
    from multiprocessing.util import Finalize
    from os import getpid
    borrowed = publication._WORKER_SKY
    def receipt():
        assert borrowed.stars._stellar_realization._closed
        (Path(directory) / f'closed-{getpid()}.txt').write_text('closed')
    Finalize(None, receipt, exitpriority=9)


@pytest.mark.parametrize('motion_document', [dict(change=dict(ra=7.5,pmra=100.,pmdec=200.),
    extra_photometry={9:3.})], indirect=True)
@pytest.mark.parametrize('epoch', [2000., -8000.])
@pytest.mark.parametrize('jobs', [1, 2])
@pytest.mark.parametrize('frame_axes', [None, 'mean-equator-equinox', 'mean-ecliptic-equinox'])
def test_stellar_motion_publication_serial_spawn_sheet_and_count_parity(motion_document, monkeypatch, epoch, jobs, frame_axes):
    _assert_stellar_publication_parity(motion_document, monkeypatch, epoch, jobs, frame_axes)


def _assert_stellar_publication_parity(motion_document, monkeypatch, epoch, jobs, frame_axes, saved=False):
    """Synthetic snapshot seam, real command/SDK/exports/book; detects static counts."""
    from pathlib import Path
    from hashlib import sha256
    from PIL import Image
    import numpy as np
    from wenu.charts import atlas_publication as publication
    from wenu.charts.atlas_sheet import AtlasSheetChartRequest, AtlasChartPresentation
    from wenu.charts.request_generation import generate_chart_request
    from wenu.charts.stellar_sizing_report import catalogue_star_counts
    from wenu.sky.assembly import stellar_realization_sky
    from wenu.sky import native_snapshot
    from wenu.atlas_design import AtlasBandTiling
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from wenu.stellar_epoch_consumer import StellarEpochViewInput, stellar_epoch_view_identity
    source, directory, write = motion_document
    config = write(lambda d: d.update(target_jyear_tcb=epoch))
    root = config.parent
    design = Path(__file__).resolve().parents[1] / 'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json'
    design_digest = sha256(design.read_bytes()).hexdigest()
    sky = _motion_cli_sky(source, root)
    class SyntheticSnapshot:
        manifest_sha256 = 'a'*64
        def require(self, **kwargs): assert kwargs['design_sha256'] == design_digest
        def make_sky(self): return sky
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot', lambda *a, **k: SyntheticSnapshot())
    if jobs == 2:
        monkeypatch.setattr(publication, '_initialize_atlas_worker', _synthetic_publication_worker)
    presentation = AtlasChartPresentation(layers=('stars','constellation_lines','constellation_labels'),
        formats=('png','pdf','svg'), dpi=36, legend_fontsize=6., report_label_scale=1.)
    bundle = root / 'synthetic-snapshot'
    bundle.mkdir()
    index = None
    if jobs == 1 and epoch == 2000.:
        from matplotlib.figure import Figure
        index = root / 'index.pdf'
        figure = Figure(figsize=(6,4))
        figure.text(.5,.5,'Synthetic static index')
        for suffix in ('png','pdf','svg'):
            figure.savefig(index.with_suffix('.'+suffix))
        index_bytes = index.read_bytes()
    frame_options = {}; orientation = None
    if frame_axes is not None:
        from test_atlas_cli import _atlas_frame_document
        from wenu.charts.atlas_sheet import load_atlas_frame
        frame_config = root / 'frame.toml'
        # Deliberately independent TT and TCB labels: orientation is not motion.
        frame_config.write_bytes(_atlas_frame_document(frame_axes, -8000 if epoch == 2000 else 2000))
        orientation = load_atlas_frame(frame_config.read_bytes())
        frame_options['atlas_frame_config'] = frame_config
    epoch_options = dict(stellar_motion_config=config)
    motion = bridge.load_stellar_motion_request(config)
    identity = bridge.stellar_motion_identity
    if saved:
        anchor = replace(motion, instant=TimePoint(2451545,0.,'tcb'))
        epoch_directory = root/'epoch'
        digest = prepare_stellar_epoch(anchor, epoch_directory)
        product = load_stellar_epoch(epoch_directory, expected_manifest_sha256=digest)
        event = motion.instant
        window = 100 if epoch == 2000 else 0
        if epoch == 2000:
            event = TimePoint(event.jd1+1,event.jd2,'tcb')
        config = root/'epoch-query.toml'
        config.write_bytes(_epoch_consumer_document(epoch_directory,digest,event,window))
        epoch_options = dict(stellar_epoch_config=config)
        motion = StellarEpochViewInput(product,event,window)
        identity = stellar_epoch_view_identity
    output = root / 'batch' 
    manifest_path = publication.create_atlas(design, output, presentation=presentation,
        charts='22,23', jobs=jobs, from_sky=bundle, index=index, **epoch_options, **frame_options)
    manifest = json.loads(manifest_path.read_text())
    assert manifest['stellar_realization'] == dict(identity(motion),
        model_counts={'full-input-rectilinear':2, 'proper-motion-angular':3,
                      'hipparcos2-angular-fallback':1, 'unavailable':3})
    if orientation is not None:
        from wenu.charts.atlas_sheet import atlas_frame_record
        assert manifest['atlas_frame'] == atlas_frame_record(orientation)
        assert manifest['atlas_frame_execution_input_sha256']
        assert all(v['frame_sha256'] == orientation.model.configuration_digest for v in manifest['derived_views'])
    assert manifest['charts'] == [22,23]
    assert manifest['workers'] == jobs
    assert not hasattr(sky.stars, '_stellar_realization')
    with stellar_realization_sky(sky, motion) as view:
        expected, ids, _ = catalogue_star_counts(view.stars, presentation.star_magnitude_limit)
    count = json.loads((output / 'atlas-star-counts.json').read_text())
    assert count['selected_count'] == expected['selected_count'] == 1
    assert catalogue_star_counts(sky.stars, presentation.star_magnitude_limit)[0]['selected_count'] == 2
    assert count['invalid_count'] == expected['invalid_count']
    assert count['provenance']['stellar_realization'] == manifest['stellar_realization']
    atlas = AtlasBandTiling.from_json(design.read_text())
    for number in (22,23):
        request = AtlasSheetChartRequest(atlas.geometry.sheets[number-1], atlas.geometry.page,
            presentation, root / f'direct-{number}', stellar_motion=motion, orientation=orientation, design_sha256=design_digest, design_bytes=design.read_bytes())
        generate_chart_request(request, sky=sky)
        stem = f'chart-{number:02d}'
        for suffix in ('', '_report'):
            with Image.open(output / (stem+suffix+'.png')) as actual, Image.open(request.output_dir / (stem+suffix+'.png')) as reference:
                np.testing.assert_array_equal(np.asarray(actual), np.asarray(reference))
        actual = json.loads((output / (stem+'_report_data.json')).read_text())['stellar_realization']
        assert all(actual[k] == v for k,v in identity(motion).items())
    from pypdf import PdfReader
    pdf = PdfReader(output / 'atlas.pdf')
    if index is not None:
        assert index.read_bytes() == index_bytes == (output/'atlas-index.pdf').read_bytes()
        if orientation is not None:
            assert 'frame/date unverified' in pdf.pages[0].extract_text()
            assert manifest['index_reference']['frame_and_date_verified'] is False
            assert manifest['index_reference']['stellar_epoch_updated'] is False
        else:
            assert 'Supplied static reference index' in pdf.pages[0].extract_text()
            assert manifest['index_reference']['stellar_epoch_updated'] is False
    assert len(pdf.pages) == len(manifest['page_order'])
    assert all(float(p.mediabox.width) == pytest.approx(atlas.geometry.page.width_mm*72/25.4) for p in pdf.pages)
    if jobs == 2:
        assert list(bundle.glob('closed-*.txt'))


@pytest.mark.parametrize('fault', ['none', 'design', 'source-sky', 'finalizer', 'warm-sdk'])
def test_stellar_publication_worker_scope_cleanup_and_refusal(motion_document, monkeypatch, fault):
    from wenu_kernel import KernelSession
    from pathlib import Path
    from wenu.charts import atlas_publication as publication
    from wenu.sky import native_snapshot
    from wenu.atlas_design import AtlasBandTiling
    import multiprocessing.util
    source, directory, write = motion_document
    config = write()
    descriptor, _ = bridge.StellarMotionExecutionInput.capture(config,
        snapshot_sha256='a'*64, design_sha256='b'*64)
    sky = _motion_cli_sky(source, config.parent)
    if fault == 'source-sky':
        sky.stars.source_catalog.loc[1, 'magnitude'] = 99.
    class SyntheticSnapshot:
        manifest_sha256 = 'a'*64
        def require(self, **kwargs):
            if kwargs['design_sha256'] != 'b'*64: raise ValueError('design mismatch')
        def make_sky(self): return sky
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot', lambda *a, **k: SyntheticSnapshot())
    closed = []
    close = bridge._StellarRealization.close
    def track(value):
        close(value); closed.append(value)
    monkeypatch.setattr(bridge._StellarRealization, 'close', track)
    def command(argv, **kwargs):
        view = kwargs['sky']
        assert kwargs['atlas_request'].stellar_motion is view.stars._stellar_realization.request
        view.stars.native_positions()
        return 0
    if fault == 'finalizer':
        def refuse(*a, **k): raise RuntimeError('synthetic finalizer registration failure')
        monkeypatch.setattr(multiprocessing.util, 'Finalize', refuse)
    if fault in ('design','source-sky','finalizer'):
        with pytest.raises((ValueError, RuntimeError)):
            publication._initialize_atlas_worker(str(directory), 'a'*64, command,
                descriptor, 'c'*64 if fault=='design' else 'b'*64)
        assert publication._WORKER_SKY is None and publication._WORKER_SCOPE is None
        assert all(v._closed for v in closed)
        return
    try:
        publication._initialize_atlas_worker(str(directory), 'a'*64, command, descriptor, 'b'*64)
        view = publication._WORKER_SKY
        atlas = AtlasBandTiling.from_json((Path(__file__).resolve().parents[1] /
            'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json').read_text())
        task = (atlas.geometry.sheets[0], atlas.geometry.page, publication.AtlasChartPresentation(), str(config.parent))
        publication._render_atlas_sheet(task)
        if fault == 'warm-sdk':
            def refuse(*a, **k): raise RuntimeError('synthetic warm refusal')
            monkeypatch.setattr(KernelSession, 'evaluate', refuse)
            with pytest.raises(RuntimeError, match='warm refusal'):
                publication._render_atlas_sheet(task)
        else:
            publication._render_atlas_sheet(task)
            assert view.stars._stellar_realization.report()['exact_batch_reuses'] > 0
    finally:
        publication._close_atlas_worker()
    assert closed and all(v._closed for v in closed)
    assert publication._WORKER_SKY is None
    assert not hasattr(sky.stars, '_stellar_realization')


def _refuse_motion_publication_sheet(argv, **kwargs):
    raise RuntimeError('synthetic publication render refusal')


@pytest.mark.parametrize('jobs', [1,2])
def test_stellar_motion_publication_failure_has_no_completion(motion_document, monkeypatch, jobs):
    from pathlib import Path
    from wenu.charts import atlas_publication as publication
    from wenu.sky import native_snapshot
    import os
    source, directory, write = motion_document
    config = write()
    root = config.parent
    sky = _motion_cli_sky(source, root)
    class SyntheticSnapshot:
        manifest_sha256 = 'a'*64
        def require(self, **kwargs): pass
        def make_sky(self): return sky
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot', lambda *a, **k: SyntheticSnapshot())
    if jobs == 2:
        monkeypatch.setattr(publication, '_initialize_atlas_worker', _synthetic_publication_worker)
    design = Path(__file__).resolve().parents[1] / 'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json'
    bundle = root/'synthetic-snapshot';bundle.mkdir()
    output = root/'batch'
    previous = {key: os.environ.get(key) for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    with pytest.raises(RuntimeError, match='render refusal'):
        publication.create_atlas(design, output, presentation=publication.AtlasChartPresentation(layers=('stars',)),
            charts='1,14', jobs=jobs, from_sky=bundle, stellar_motion_config=config,
            chart_command=_refuse_motion_publication_sheet)
    assert not output.exists()
    assert not list(root.glob('.wenu-atlas-pages-*'))
    assert all(os.environ.get(k) == v for k,v in previous.items())
    assert not hasattr(sky.stars, '_stellar_realization')
    if jobs == 2: assert list(bundle.glob('closed-*.txt'))


@pytest.mark.parametrize('fault', ['epoch','cleanup'])
def test_stellar_publication_rejects_returned_epoch_or_cleanup_failure(motion_document, monkeypatch, fault):
    from pathlib import Path
    from wenu.charts import atlas_publication as publication
    from wenu.sky import native_snapshot
    source, directory, write = motion_document
    config = write(); root = config.parent
    sky = _motion_cli_sky(source, root)
    class SyntheticSnapshot:
        manifest_sha256 = 'a'*64
        def require(self, **kwargs): pass
        def make_sky(self): return sky
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot', lambda *a, **k: SyntheticSnapshot())
    render = publication._render_atlas_sheet
    def wrong_epoch(task, *args, **kwargs):
        result = render(task, *args, **kwargs)
        path = Path(task[3]) / f'chart-{result:02d}_report_data.json'
        report = json.loads(path.read_text())
        if fault == 'epoch':
            report['stellar_realization']['epoch']['jd1'] += 1
        path.write_text(json.dumps(report))
        return result
    monkeypatch.setattr(publication, '_render_atlas_sheet', wrong_epoch)
    if fault == 'cleanup':
        close = bridge._StellarRealization.close
        def failed_close(value):
            close(value)
            raise RuntimeError('synthetic cleanup failure')
        monkeypatch.setattr(bridge._StellarRealization, 'close', failed_close)
    design = Path(__file__).resolve().parents[1] / 'src/wenu/configuration/presets/atlas_layout_b4_portrait_v3.json'
    bundle = root/'synthetic-snapshot';bundle.mkdir()
    with pytest.raises(ValueError if fault=='epoch' else RuntimeError,
            match='different stellar motion identity' if fault=='epoch' else 'cleanup failure'):
        publication.create_atlas(design, root/'batch', jobs=1, charts='22,23', from_sky=bundle,
            stellar_motion_config=config, presentation=publication.AtlasChartPresentation(layers=('stars',),dpi=36))
    assert not (root/'batch').exists()
    assert not list(root.glob('.wenu-atlas-pages-*'))



def _epoch_request(source):
    return _production_motion(source, TimePoint(2451545, .125, 'tcb'))


def test_stellar_epoch_selection_matches_live_realization(motion_source, tmp_path):
    import pandas as pd
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from wenu_kernel.errors import ClosedSession
    request = _epoch_request(motion_source())
    source = request.catalogues[0].source
    stars = tuple(source.records())
    table = pd.DataFrame({'magnitude': [s['original']['magnitude'] for s in stars]},
                         index=list(range(1, 10)))
    for selected in (tuple(range(1, 10)), (8, 1, 5, 4), ()):
        live = bridge._StellarRealization(request, table.loc[list(selected)], source.metadata['original_metadata'])
        try:
            metadata = live.row_metadata(selected)
            selection = bridge.stellar_model_selection(request, selected)
            assert list(metadata['stellar_motion_model']) == [
                None if i is None else request.catalogues[i].motion_policy for _, i, _ in selection]
            assert list(metadata['stellar_motion_reason']) == [
                ';'.join(reasons) if i is None else '' for _, i, reasons in selection]
            live.positions(selected)
            live.positions(selected)
            if selected:
                assert live.report()['exact_batch_reuses'] > 0
        finally:
            live.close()
        with unittest.TestCase().assertRaises(ClosedSession):
            live.positions(selected)
    destination = tmp_path/'selection'
    prepare_stellar_epoch(request, destination)
    result = load_stellar_epoch(destination)
    assert [(r['identifier'], r['model_index'], tuple(r['reasons'])) for r in result.rows()] == list(
        bridge.stellar_model_selection(request))


def test_stellar_epoch_mixed_roundtrip_matches_direct_sdk_and_preserves_sources(motion_source, tmp_path):
    from dataclasses import asdict, FrozenInstanceError
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from wenu_kernel.records import ObjectKey
    request = _epoch_request(motion_source())
    destination = tmp_path/'epoch'
    digest = prepare_stellar_epoch(request, destination)
    product = load_stellar_epoch(destination, expected_manifest_sha256=digest)
    rows = product.at(request.instant)
    assert [r['identifier'] for r in rows] == list(map(str, range(1, 10)))
    assert [r['model_index'] for r in rows] == [0, 1, 1, None, 2, 0, None, 1, None]
    assert [r['identifier'] for r in rows if r['cartesian'] is not None] == ['1', '6']
    assert product.source.manifest == request.catalogues[0].source.manifest
    assert product.source.products == request.catalogues[0].source.products
    sources = {s['source_id']: s for s in product.source.records('gaia_sources_v1.jsonl')}
    assert sources['9007199254740994']['parallax'] == 100.  # missing RV is not zero parallax
    assert sources['9007199254740995']['parallax'] == -1.   # retain measured negative value
    assert sources['9007199254741000']['parallax'] == 0.
    for index, catalogue in enumerate(request.catalogues):
        for representation in ('direction', 'cartesian') if index == 0 else ('direction',):
            provider = bridge.StellarMotionProvider(catalogue, representation=representation)
            admission = provider.describe().admissions[0]
            chosen = [r for r in rows if r['model_index'] == index]
            query = StateQuery(admission.catalogue, admission.model,
                tuple(ObjectKey('hipparcos:' + r['identifier']) for r in chosen),
                (request.instant,), admission.reference,
                AccuracyRequest(metric='euclidean_norm') if representation == 'cartesian' else AccuracyRequest(),
                require_velocity=representation == 'cartesian')
            with Kernel(references=(admission.reference,)) as kernel:
                kernel.register(provider, ownership='owned')
                with kernel.open_session(SessionPolicy((admission.catalogue,))) as session:
                    direct = session.evaluate(query)
            for row, state in zip(chosen, direct.states, strict=True):
                assert row[representation] == json.loads(json.dumps(asdict(state)))
        stored = product.models()[index]
        for row, original in zip(stored['coefficients'], catalogue.rows, strict=True):
            assert row['source_epoch'] == (None if original.source_epoch is None else
                [original.source_epoch.jd1, original.source_epoch.jd2, original.source_epoch.scale])
            assert row['initial'] == (None if original.unavailable_reason else
                list(original.position_m if index == 0 else original.direction))
            assert row['derivative'] == (None if original.unavailable_reason else
                list(original.velocity_m_s if index == 0 else original.tangent_per_s))
    assert [r['identifier'] for r in product.at(request.instant, ('5', '2'))] == ['5', '2']
    detached = product.at(request.instant, ('1',))[0]
    detached['direction']['vector'][0] = 999.
    assert product.at(request.instant, ('1',))[0] != detached
    checker = unittest.TestCase()
    with checker.assertRaises(FrozenInstanceError):
        product.states_payload = b'changed'
    for instant in (TimePoint(2451545, .126, 'tcb'), TimePoint(2451545, .125, 'tdb'), None):
        with checker.assertRaisesRegex(ValueError, 'Exact saved TCB event'):
            product.at(instant)
    for ids in (('1', '1'), ('999',), (1,)):
        with checker.assertRaises(ValueError):
            product.at(request.instant, ids)


def test_stellar_epoch_fresh_process_load_needs_no_source_path_or_provider(motion_source, tmp_path):
    import os
    from pathlib import Path
    import shutil
    import subprocess
    import sys
    import wenu_kernel
    from wenu.stellar_enrichment import load_stellar_enrichment
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from hashlib import sha256
    source = motion_source()
    external = tmp_path/'original-source'
    external.mkdir()
    for name, raw in source.products:
        (external/name).write_bytes(raw)
    (external/'source_manifest_v1.json').write_bytes(source.manifest)
    request = _epoch_request(load_stellar_enrichment(external))
    destination = tmp_path/'epoch'
    digest = prepare_stellar_epoch(request, destination)
    expected = sha256(load_stellar_epoch(destination).states_payload).hexdigest()
    shutil.rmtree(external)
    script = '''
import sys
from hashlib import sha256
from unittest.mock import patch
from wenu import stellar_state
from wenu_kernel import Kernel
from wenu.stellar_epoch import load_stellar_epoch
with patch.object(stellar_state.StellarMotionProvider, '__init__', side_effect=AssertionError('provider constructed')), patch.object(Kernel, 'open_session', side_effect=AssertionError('session created')):
    product = load_stellar_epoch(sys.argv[1], expected_manifest_sha256=sys.argv[2])
    assert len(product.at(product.instant)) == 9
    assert sha256(product.states_payload).hexdigest() == sys.argv[3]
print('fresh exact reload without provider/source path')
'''
    # Keep installed dependencies on Python's normal site path. Prepending
    # site-packages can let backports shadow the standard library (e.g. pathlib).
    paths = [str(Path(bridge.__file__).parents[1]), os.environ.get('PYTHONPATH', '')]
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in paths if p))
    result = subprocess.run([sys.executable, '-c', script, str(destination), digest, expected],
        env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'fresh exact reload without provider/source path'


def test_stellar_epoch_rejects_corruption_and_semantic_mismatches(motion_source, tmp_path):
    from pathlib import Path
    import shutil
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from wenu.stellar_enrichment import decode, encode, identity
    checker = unittest.TestCase()
    original = tmp_path/'baseline'
    digest = prepare_stellar_epoch(_epoch_request(motion_source()), original)
    def reseal(root, name, raw):
        (root/name).write_bytes(raw)
        manifest = decode((root/'manifest.json').read_bytes())
        manifest['products'][name] = identity(raw)
        (root/'manifest.json').write_bytes(encode(manifest))
    faults = ('hip', 'priority', 'event', 'reference', 'units', 'angular_pv', 'gap',
              'coefficient', 'model_order', 'schema', 'missing', 'truncated', 'source',
              'state_bytes', 'duplicate_json', 'symlink')
    for fault in faults:
        root = tmp_path/fault
        shutil.copytree(original, root)
        rows = [decode(line) for line in (root/'states.jsonl').read_bytes().splitlines()]
        if fault == 'hip': rows[0]['identifier'] = '999'
        elif fault == 'priority': rows[0]['model_index'] = 1
        elif fault == 'event': rows[0]['direction']['time']['jd2'] = .126
        elif fault == 'reference': rows[0]['direction']['reference']['origin_id'] = 'earth'
        elif fault == 'units': rows[0]['direction']['reference']['units'] = 'deg'
        elif fault == 'angular_pv': rows[1]['cartesian'] = rows[0]['cartesian']
        elif fault == 'gap': rows[3]['direction'] = rows[0]['direction']
        elif fault == 'coefficient':
            models = decode((root/'models.json').read_bytes())
            models[0]['coefficients'][0]['derivative'][0] += 1.
            reseal(root, 'models.json', encode(models))
        elif fault == 'model_order':
            manifest = decode((root/'manifest.json').read_bytes())
            manifest['motion_identity']['model_order'].reverse()
            (root/'manifest.json').write_bytes(encode(manifest))
        elif fault == 'schema':
            manifest = decode((root/'manifest.json').read_bytes())
            manifest['schema'] = 'unknown/999'
            (root/'manifest.json').write_bytes(encode(manifest))
        elif fault == 'missing': (root/'models.json').unlink()
        elif fault == 'truncated':
            reseal(root, 'states.jsonl', (root/'states.jsonl').read_bytes()[:-1])
        elif fault == 'source':
            raw = (root/'source/stars_v1.jsonl').read_bytes().replace(b'"magnitude":2.0', b'"magnitude":3.0')
            assert raw != (root/'source/stars_v1.jsonl').read_bytes()
            reseal(root, 'source/stars_v1.jsonl', raw)
        elif fault == 'state_bytes':
            (root/'states.jsonl').write_bytes((root/'states.jsonl').read_bytes().replace(b'"evaluated"', b'"altered"', 1))
        elif fault == 'duplicate_json':
            (root/'manifest.json').write_bytes(b'{"schema":"x",' + (root/'manifest.json').read_bytes()[1:])
        elif fault == 'symlink':
            (root/'models.json').unlink()
            (root/'models.json').symlink_to(original/'models.json')
        if fault in ('hip', 'priority', 'event', 'reference', 'units', 'angular_pv', 'gap'):
            reseal(root, 'states.jsonl', b''.join(encode(r)+b'\n' for r in rows))
        with checker.assertRaises((ValueError, OSError), msg=fault):
            load_stellar_epoch(root)
        with checker.assertRaises((ValueError, OSError), msg='pinned ' + fault):
            load_stellar_epoch(root, expected_manifest_sha256=digest)


def test_stellar_epoch_publication_refusal_and_partial_cleanup(motion_source, tmp_path):
    from unittest.mock import patch
    from pathlib import Path
    import os
    from wenu import stellar_epoch
    checker = unittest.TestCase()
    request = _epoch_request(motion_source())
    existing = tmp_path/'existing'
    existing.mkdir()
    (existing/'unique-input').write_bytes(b'preserve me')
    with checker.assertRaises(FileExistsError):
        stellar_epoch.prepare_stellar_epoch(request, existing)
    assert (existing/'unique-input').read_bytes() == b'preserve me'
    from wenu_kernel.errors import ProviderEvaluationError
    for fault in ('evaluation', 'link', 'manifest_link', 'validation', 'race'):
        destination = tmp_path/fault
        original_link = os.link
        def failing_link(src, dst):
            if fault == 'link' or Path(dst).name == 'manifest.json':
                raise RuntimeError('injected publication failure')
            return original_link(src, dst)
        original_loader = stellar_epoch.load_stellar_epoch
        def staged_load(*args, **kwargs):
            result = original_loader(*args, **kwargs)
            if fault == 'race':
                destination.mkdir()
                (destination/'unique-input').write_bytes(b'other owner')
            return result
        if fault == 'evaluation':
            context = patch.object(bridge.StellarMotionProvider, 'evaluate', side_effect=RuntimeError('injected evaluation failure'))
        elif fault == 'validation':
            context = patch.object(stellar_epoch, 'load_stellar_epoch', side_effect=RuntimeError('injected validation failure'))
        elif fault == 'race':
            context = patch.object(stellar_epoch, 'load_stellar_epoch', side_effect=staged_load)
        else:
            context = patch.object(os, 'link', side_effect=failing_link)
        with context, checker.assertRaises((RuntimeError, FileExistsError, ProviderEvaluationError)):
            stellar_epoch.prepare_stellar_epoch(request, destination)
        if fault == 'race':
            assert (destination/'unique-input').read_bytes() == b'other owner'
        else:
            assert not destination.exists()
        assert not list(tmp_path.glob('.wenu-stellar-epoch-*'))


def test_stellar_epoch_offline_preparation_command(motion_source, tmp_path):
    from hashlib import sha256
    from pathlib import Path
    import os
    import subprocess
    import sys
    import wenu_kernel
    from wenu.stellar_epoch import load_stellar_epoch
    source = motion_source()
    directory = tmp_path/'source'
    directory.mkdir()
    for name, raw in source.products:
        (directory/name).write_bytes(raw)
    (directory/'source_manifest_v1.json').write_bytes(source.manifest)
    config = tmp_path/'motion.toml'
    config.write_text('''schema_version = 1
document_kind = "wenu-stellar-motion-request"
source_directory = "source"
target_jyear_tcb = 2000.0
source_manifest_sha256 = "''' + sha256(source.manifest).hexdigest() + '''"
[[models]]
motion_policy = "proper-motion-angular"
distance_policy = "not-used"
radial_velocity_policy = "not-used"
start_jyear_tcb = -8001.0
stop_jyear_tcb = 2050.0
''')
    destination = tmp_path/'command-result'
    tool = Path(__file__).resolve().parents[1]/'tools/prepare_stellar_epoch.py'
    # Keep installed dependencies on Python's normal site path. Prepending
    # site-packages can let backports shadow the standard library (e.g. pathlib).
    paths = [str(Path(bridge.__file__).parents[1]), os.environ.get('PYTHONPATH', '')]
    environment = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in paths if p))
    command = [sys.executable, str(tool), '--stellar-motion-config', str(config), '--destination', str(destination)]
    result = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    product = load_stellar_epoch(destination, expected_manifest_sha256=receipt['manifest_sha256'])
    assert product.instant == TimePoint(2451545, 0., 'tcb')
    assert len(product.at(product.instant)) == 9
    assert all(row['cartesian'] is None for row in product.rows())
    before = (destination/'manifest.json').read_bytes()
    retry = subprocess.run(command, env=environment, capture_output=True, text=True)
    assert retry.returncode != 0 and 'FileExistsError' in retry.stderr
    assert (destination/'manifest.json').read_bytes() == before



def _epoch_query_product(source, tmp_path):
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    request = _epoch_request(source)
    prepare_stellar_epoch(request, tmp_path/'anchor')
    return load_stellar_epoch(tmp_path/'anchor'), request


def test_stellar_epoch_query_reuse_boundaries_and_native_inputs(motion_source, tmp_path):
    """Protect inclusive signed boundaries and real split-JD, not rounded years."""
    from dataclasses import asdict
    from decimal import Decimal
    from fractions import Fraction
    from math import nextafter
    from unittest.mock import patch
    from wenu import stellar_epoch_query as query
    product, request = _epoch_query_product(motion_source(), tmp_path)
    checker = unittest.TestCase()
    anchor = product.instant
    def resolve(event, window=4):
        return query.resolve_stellar_epoch(product, event, reuse_window_julian_years=window)
    # Reuse is prohibited from reconstructing models or opening SDK resources.
    with patch.object(query, '_restore', side_effect=AssertionError('model reconstruction')), \
         patch.object(bridge, 'StellarMotionProvider', side_effect=AssertionError('provider')), \
         patch.object(Kernel, 'open_session', side_effect=AssertionError('session')):
        for sign in (-1, 1):
            for fraction in (.125, nextafter(.125, 0. if sign > 0 else 1.)):
                event = TimePoint(anchor.jd1 + sign*1461, fraction, 'tcb')
                result = resolve(event)
                assert tuple(result.rows()) == product.at(anchor)
                receipt = result.receipt()
                assert receipt['mode'] == 'reused'
                assert receipt['requested_event'] == asdict(event)
                assert receipt['actual_position_event'] == asdict(anchor)
                assert receipt['approximation']['kind'] == 'fixed-position'
        for window in (0, 0., Fraction(1, 7), Decimal('0.1')):
            assert resolve(anchor, window).receipt()['mode'] == 'reused'
    for sign in (-1, 1):
        event = TimePoint(anchor.jd1 + sign*1461, nextafter(.125, 1. if sign > 0 else 0.), 'tcb')
        assert resolve(event).receipt()['mode'] == 'advanced'
    # A fraction smaller than the ULP of the summed JD must not disappear.
    event = TimePoint(anchor.jd1, nextafter(anchor.jd2, 1.), 'tcb')
    assert resolve(event, 0).receipt()['mode'] == 'advanced'
    for bad in (True, False, -1, '4', None, float('nan'), float('inf'), -float('inf'), complex(1)):
        with checker.assertRaises(ValueError):
            resolve(anchor, bad)
    for bad in (TimePoint(anchor.jd1, anchor.jd2, 'tdb'), None):
        with checker.assertRaises(ValueError):
            resolve(bad)
    with checker.assertRaises(TypeError):
        query.resolve_stellar_epoch(product, anchor)
    with checker.assertRaises(ValueError):
        query.resolve_stellar_epoch(resolve(anchor), anchor, reuse_window_julian_years=4)


def test_stellar_epoch_query_coverage_subset_and_detached_data(motion_source, tmp_path):
    from dataclasses import asdict, FrozenInstanceError
    from unittest.mock import patch
    from wenu import stellar_epoch_query as query
    product, request = _epoch_query_product(motion_source(), tmp_path)
    checker = unittest.TestCase()
    event = TimePoint(3000001, 0., 'tcb')
    # Fixed-position reuse across a domain edge discloses lack of target coverage.
    result = query.resolve_stellar_epoch(product, event, reuse_window_julian_years=2000, identifiers=('5', '2', '4'))
    assert [r['identifier'] for r in result.rows()] == ['5', '2', '4']
    assert result.receipt()['actual_position_event'] == asdict(product.instant)
    assert all(not r['contains_requested_event'] for r in result.receipt()['requested_event_model_coverage'])
    with checker.assertRaisesRegex(ValueError, 'original stellar model domain'):
        query.resolve_stellar_epoch(product, event, reuse_window_julian_years=0)
    for ids in (('1', '1'), ('999',), (1,)):
        with checker.assertRaises(ValueError):
            query.resolve_stellar_epoch(product, product.instant, reuse_window_julian_years=0, identifiers=ids)
    with patch.object(Kernel, 'open_session', side_effect=AssertionError('empty query')):
        for event in (product.instant, TimePoint(2457389, 0., 'tcb')):
            empty = query.resolve_stellar_epoch(product, event, reuse_window_julian_years=0, identifiers=())
            assert tuple(empty.rows()) == () and empty.receipt()['identifiers'] == []
    assert result.source is product.source
    rows = tuple(result.rows()); rows[0]['direction']['vector'][0] = 999
    receipt = result.receipt(); receipt['requested_event']['jd1'] = 0
    assert tuple(result.rows())[0] != rows[0] and result.receipt() != receipt
    with checker.assertRaises(FrozenInstanceError):
        result.source = None
    with checker.assertRaisesRegex(ValueError, 'Exact saved TCB'):
        product.at(event)


def test_stellar_epoch_query_advancement_matches_original_sdk_and_never_slides(motion_source, tmp_path):
    """Compare all mixed-model states with the unchanged direct-SDK preparation."""
    from dataclasses import replace
    from unittest.mock import patch
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from wenu import stellar_epoch_query as query
    source = motion_source(change=dict(pmra=1e8, pmdec=-1e8, radial_velocity=None), hip2_change=dict(pmRA=1e5))
    product, request = _epoch_query_product(source, tmp_path)
    before = (product.manifest, product.models_payload, product.states_payload, product.source.products)
    targets = (TimePoint(2457389, 0., 'tcb'), TimePoint(-1200955, 0., 'tcb'))
    expected = {}
    for i, event in enumerate(targets):
        prepare_stellar_epoch(replace(request, instant=event), tmp_path/str(i))
        expected[event] = tuple(load_stellar_epoch(tmp_path/str(i)).rows())
        result = query.resolve_stellar_epoch(product, event, reuse_window_julian_years=1)
        assert tuple(result.rows()) == expected[event]
        assert result.receipt()['mode'] == 'advanced'
        assert result.source is product.source
        assert result.source.products == source.products
        assert [r['model_index'] for r in result.rows()] == [r['model_index'] for r in product.rows()]
        subset = query.resolve_stellar_epoch(product, event, reuse_window_julian_years=1, identifiers=('5','2','1','4'))
        lookup = {r['identifier']: r for r in expected[event]}
        assert tuple(subset.rows()) == tuple(lookup[i] for i in ('5','2','1','4'))
    for event in (targets[1], product.instant, targets[0], product.instant):
        result = query.resolve_stellar_epoch(product, event, reuse_window_julian_years=1)
        assert tuple(result.rows()) == (product.at(product.instant) if event == product.instant else expected[event])
    # Sliding-anchor and stale-outside-window faults must fail this successful baseline.
    edge = TimePoint(product.instant.jd1 + 365, product.instant.jd2, 'tcb')
    outside = TimePoint(product.instant.jd1 + 366, product.instant.jd2, 'tcb')
    assert query.resolve_stellar_epoch(product, edge, reuse_window_julian_years=1).receipt()['mode'] == 'reused'
    assert query.resolve_stellar_epoch(product, outside, reuse_window_julian_years=1).receipt()['mode'] == 'advanced'
    checker = unittest.TestCase()
    original_day = query._day
    def assert_original_anchor():
        assert query.resolve_stellar_epoch(product, outside, reuse_window_julian_years=1).receipt()['mode'] == 'advanced'
    assert_original_anchor()
    with patch.object(query, '_day', side_effect=lambda t: original_day(edge if t == product.instant else t)):
        with checker.assertRaises(AssertionError):
            assert_original_anchor()
    def assert_target():
        assert tuple(query.resolve_stellar_epoch(product, targets[0], reuse_window_julian_years=1).rows()) == expected[targets[0]]
    assert_target()
    with patch.object(query, '_advance', return_value=product.states_payload):
        with checker.assertRaises(AssertionError):
            assert_target()
    # Saved states relabeled as the requested epoch also fail byte identity.
    from wenu.stellar_enrichment import encode
    relabeled = list(product.rows())
    for row in relabeled:
        for kind in ('direction', 'cartesian'):
            if row[kind]:
                row[kind]['time'] = dict(jd1=targets[0].jd1, jd2=targets[0].jd2, scale='tcb')
                row[kind]['anchor_time'] = row[kind]['time']
    with patch.object(query, '_advance', return_value=b''.join(encode(r)+b'\n' for r in relabeled)):
        with checker.assertRaises(AssertionError):
            assert_target()
    assert before == (product.manifest, product.models_payload, product.states_payload, product.source.products)
    values = list(result.source.records('gaia_sources_v1.jsonl'))
    assert {r['parallax'] for r in values} >= {100., -1., 0.}


def test_stellar_epoch_query_refuses_changed_admission_coefficients_and_rebasing(motion_source, tmp_path):
    from dataclasses import replace
    from unittest.mock import patch
    from wenu import stellar_epoch_query as query
    source = motion_source(change=dict(pmra=1e8, pmdec=-1e8, radial_velocity=None))
    product, request = _epoch_query_product(source, tmp_path)
    target = TimePoint(2457389, 0., 'tcb')
    resolve = lambda: query.resolve_stellar_epoch(product, target, reuse_window_julian_years=0)
    baseline = tuple(resolve().rows())
    checker = unittest.TestCase()
    original = bridge.admit_stellar_angular_motion
    def changed(*args, **kwargs):
        current = original(*args, **kwargs)
        rows = list(current.rows)
        row = rows[0]
        rows[0] = replace(row, tangent_per_s=tuple(2*v for v in row.tangent_per_s))
        object.__setattr__(current, 'rows', tuple(rows))
        return current
    with patch.object(bridge, 'admit_stellar_angular_motion', side_effect=changed):
        with checker.assertRaisesRegex(ValueError, 'coefficients differ'):
            resolve()
    original_record = bridge.StellarMotionCatalogue.to_record
    def wrong_record(current):
        record = original_record(current); record['policies']['physical_accuracy'] = 'invented'
        return record
    with patch.object(bridge.StellarMotionCatalogue, 'to_record', wrong_record):
        with checker.assertRaisesRegex(ValueError, 'admission differs'):
            resolve()
    original_describe = bridge.StellarMotionProvider.describe
    def wrong_reference(provider):
        descriptor = original_describe(provider)
        admission = descriptor.admissions[0]
        reference = replace(admission.reference, correction_policy='changed binding')
        return replace(descriptor, admissions=(replace(admission, reference=reference),))
    with patch.object(bridge.StellarMotionProvider, 'describe', wrong_reference):
        with checker.assertRaisesRegex(ValueError, 'reference differs'):
            resolve()
    # Deliberately bypass reconstruction verification to simulate normalized-vector
    # rebasing. The direct original-model comparison must detect the wrong result.
    restore = query._restore
    def rebased(*args):
        restored = restore(*args)
        angular = restored[1]
        saved = {r['identifier']: r for r in product.rows()}
        rows = []
        for row in angular.rows:
            direction = saved[row.identifier]['direction']
            if row.unavailable_reason is None and direction is not None:
                vector = tuple(direction['vector'])
                dot = sum(v*t for v, t in zip(vector, row.tangent_per_s))
                tangent = tuple(t-dot*v for v, t in zip(vector, row.tangent_per_s))
                row = replace(row, source_epoch=product.instant, direction=vector, tangent_per_s=tangent)
            rows.append(row)
        object.__setattr__(angular, 'rows', tuple(rows))
        return restored
    with patch.object(query, '_restore', side_effect=rebased):
        assert tuple(resolve().rows()) != baseline
    assert tuple(resolve().rows()) == baseline


def test_stellar_epoch_query_failure_closes_resources_and_never_falls_back(motion_source, tmp_path):
    from unittest.mock import patch
    from wenu import stellar_epoch_query as query
    from wenu_kernel.kernel import KernelSession
    product, request = _epoch_query_product(motion_source(), tmp_path)
    target = TimePoint(2457389, 0., 'tcb')
    baseline = tuple(query.resolve_stellar_epoch(product, target, reuse_window_julian_years=0).rows())
    checker = unittest.TestCase()
    for owner, name in ((Kernel, 'register'), (Kernel, 'open_session'), (KernelSession, 'evaluate')):
        closed = []; kernels = []; sessions = []
        kernel_close = Kernel.close
        session_close = KernelSession.close
        def close_kernel(kernel):
            kernels.append(kernel)
            return kernel_close(kernel)
        def close_session(session):
            sessions.append(session)
            return session_close(session)
        original_close = bridge.StellarMotionProvider.close
        def close(provider):
            closed.append(provider)
            return original_close(provider)
        with patch.object(bridge.StellarMotionProvider, 'close', close), \
             patch.object(Kernel, 'close', close_kernel), \
             patch.object(KernelSession, 'close', close_session), \
             patch.object(owner, name, side_effect=RuntimeError('injected query failure')):
            with checker.assertRaisesRegex(RuntimeError, 'injected query failure'):
                query.resolve_stellar_epoch(product, target, reuse_window_julian_years=0)
        assert len(closed) == 1  # first failed query does not try a fallback model
        assert len(kernels) == 1 and kernels[0]._closed
        assert len(sessions) == (1 if name == 'evaluate' else 0)
        assert all(session._closed for session in sessions)
        assert tuple(query.resolve_stellar_epoch(product, target, reuse_window_julian_years=0).rows()) == baseline



def _epoch_consumer_document(product, digest, event, window=100):
    return ('schema_version = 1\ndocument_kind = "wenu-stellar-epoch-query"\n'
        f'catalogue_directory = "{product.as_posix()}"\nmanifest_sha256 = "{digest}"\n'
        f'reuse_window_julian_years = {window}\n[instant]\njd1 = {event.jd1}\n'
        f'jd2 = {event.jd2!r}\nscale = "{event.scale}"\n').encode()


def test_stellar_epoch_consumer_positions_binding_and_lifetime(motion_source, tmp_path):
    from dataclasses import FrozenInstanceError
    from unittest.mock import patch
    import numpy as np
    from wenu.stellar_epoch_consumer import StellarEpochViewInput, StellarEpochRealization
    product, original = _epoch_query_product(motion_source(), tmp_path)
    event = TimePoint(product.instant.jd1+1, product.instant.jd2, 'tcb')
    request = StellarEpochViewInput(product, event, 100)
    table = pd.DataFrame({'magnitude':[r['original']['magnitude'] for r in product.source.records()]}, index=range(1,10))
    metadata = product.source.metadata['original_metadata']
    with patch.object(bridge, 'StellarMotionProvider', side_effect=AssertionError('consumer re-evaluated')):
        view = StellarEpochRealization(request, table, metadata)
        lon, lat = view.positions((5,2,4))
        assert np.isfinite(lon[:2]).all() and np.isnan(lon[2]) and np.isnan(lat[2])
        assert view.row_metadata((5,2,4))['stellar_motion_status'].tolist() == ['evaluated','evaluated','unavailable']
        report = view.report()
        assert report['epoch'] == request.resolution.receipt()['actual_position_event']
        assert report['epoch_query']['requested_event']['jd1'] == event.jd1
        assert report['sdk_batches_evaluated'] == 0
        assert view.positions(())[0].size == 0
        detached = view.report();detached['epoch']['jd1']=0
        assert view.report()['epoch']['jd1'] != 0
    checker=unittest.TestCase()
    for key,value in [('catalogue','wrong'),('epoch',{'value':1900}),('units',{})]:
        with checker.assertRaises(ValueError):
            StellarEpochRealization(request,table,dict(metadata,**{key:value}))
    changed=table.copy();changed.loc[1,'magnitude']=99
    with checker.assertRaises(ValueError):StellarEpochRealization(request,changed,metadata)
    with checker.assertRaises(FrozenInstanceError):request.instant=event
    view.close()
    with checker.assertRaises(ClosedSession):view.positions((1,))
    assert tuple(request.resolution.rows()) == product.at(product.instant)


def test_stellar_epoch_consumer_capture_worker_binding_and_refusals(motion_source, tmp_path):
    from dataclasses import replace
    import pickle
    from wenu.stellar_epoch_consumer import StellarEpochExecutionInput, stellar_epoch_view_identity
    product, original = _epoch_query_product(motion_source(), tmp_path)
    from hashlib import sha256
    digest=sha256(product.manifest).hexdigest()
    document=tmp_path/'query.toml'
    document.write_bytes(_epoch_consumer_document(tmp_path/'anchor',digest,product.instant))
    captured, request=StellarEpochExecutionInput.capture(document,snapshot_sha256='b'*64,design_sha256='c'*64)
    document.write_text('changed after capture')
    restored=pickle.loads(pickle.dumps(captured))
    second=restored.admit(snapshot_sha256='b'*64,design_sha256='c'*64)
    assert stellar_epoch_view_identity(second) == stellar_epoch_view_identity(request)
    assert tuple(second.resolution.rows()) == tuple(request.resolution.rows())
    checker=unittest.TestCase()
    with checker.assertRaises(TypeError):pickle.dumps(request)
    for candidate in (replace(captured,document=captured.document+b'\n'),replace(captured,base_directory='/changed')):
        with checker.assertRaisesRegex(ValueError,'binding differs'):
            candidate.admit(snapshot_sha256='b'*64,design_sha256='c'*64)
    with checker.assertRaises(ValueError):captured.admit(snapshot_sha256='d'*64,design_sha256='c'*64)
    for change in (dict(manifest_sha256='0'*64),dict(unknown='field')):
        raw=_epoch_consumer_document(tmp_path/'anchor',change.get('manifest_sha256',digest),product.instant)
        if 'unknown' in change:raw=b'unknown = "field"\n'+raw
        document.write_bytes(raw)
        with checker.assertRaises(ValueError):
            StellarEpochExecutionInput.capture(document,snapshot_sha256='b'*64,design_sha256='c'*64)
    path=tmp_path/'anchor/states.jsonl';path.write_bytes(path.read_bytes()+b'\n')
    with checker.assertRaises(ValueError):captured.admit(snapshot_sha256='b'*64,design_sha256='c'*64)


def test_stellar_epoch_consumer_public_view_shares_positions_without_sdk(motion_source, tmp_path):
    from dataclasses import replace
    import numpy as np
    from wenu.stellar_epoch_consumer import StellarEpochViewInput
    from wenu.sky.assembly import stellar_realization_sky
    from wenu.sky.celestial_sphere import CelestialSphere
    from wenu.sky.constellation_lines import ConstellationLines
    from wenu.sky.constellation_labels import ConstellationLabels
    product, original = _epoch_query_product(motion_source(), tmp_path)
    sky=CelestialSphere(None);sky.stars=_production_stars(product.source)
    path=tmp_path/'lines.fab';path.write_text('Ori 1 1 2\n')
    sky.constellation_lines=ConstellationLines(sky.stars,filename=path)
    sky.constellation_labels=ConstellationLabels(sky.stars,min_stars=1)
    sky._layers=[sky.stars,sky.constellation_lines,sky.constellation_labels]
    for event,window in ((TimePoint(product.instant.jd1+1,product.instant.jd2,'tcb'),100),
                         (TimePoint(990545,0.,'tcb'),0)):
        request=StellarEpochViewInput(product,event,window)
        actual=request.resolution.receipt()['actual_position_event']
        with sky.stars.realized(replace(original,instant=TimePoint(**actual))) as live:
            expected=live.native_positions()
        with patch.object(bridge,'StellarMotionProvider',side_effect=AssertionError('render acquired provider')):
            with stellar_realization_sky(sky,request) as view:
                found=view.stars.native_positions()
                np.testing.assert_array_equal(found.ids,expected.ids)
                np.testing.assert_array_equal(found.lon_deg,expected.lon_deg)
                np.testing.assert_array_equal(found.lat_deg,expected.lat_deg)
                assert view.constellation_lines.stars is view.stars
                assert view.constellation_labels.stars is view.stars
                assert view.stars._stellar_realization.report()['epoch']==actual
        with unittest.TestCase().assertRaises(ClosedSession):view.stars.native_positions()
    assert not hasattr(sky.stars,'_stellar_realization')


@pytest.mark.parametrize('motion_document', [dict(change=dict(ra=7.5,pmra=100.,pmdec=200.), extra_photometry={9:3.})], indirect=True)
@pytest.mark.parametrize('epoch', [2000., -2000.])
@pytest.mark.parametrize('jobs', [1,2])
@pytest.mark.parametrize('frame_axes', [None,'mean-equator-equinox'])
def test_stellar_epoch_consumer_publication_serial_spawn_parity(motion_document, monkeypatch, epoch, jobs, frame_axes):
    _assert_stellar_publication_parity(motion_document, monkeypatch, epoch, jobs, frame_axes, saved=True)

@pytest.mark.parametrize('motion_document', [
    dict(change=dict(ra=7.5, pmra=100., pmdec=200.), extra_photometry={9:3.})
], indirect=True)
@pytest.mark.parametrize('target', ['reused', 'advanced'])
def test_stellar_epoch_single_sheet_cli_file_admission_and_parity(
        motion_document, tmp_path, monkeypatch, target):
    """Synthetic source/snapshot; real saved-product query, CLI, request and export."""
    from hashlib import sha256
    from PIL import Image
    import numpy as np
    from wenu.cli import chart
    from wenu.atlas_design import AtlasBandTiling
    from wenu.charts.atlas_sheet import AtlasSheetChartRequest, AtlasChartPresentation
    from wenu.charts.request_generation import generate_chart_request
    from wenu.resources import configuration_preset_path
    from wenu.sky import native_snapshot
    from wenu.stellar_epoch import prepare_stellar_epoch, load_stellar_epoch
    from wenu.stellar_epoch_consumer import StellarEpochViewInput
    from wenu.observer import Observer

    source, directory, write = motion_document
    live_config = write(lambda d: d.update(target_jyear_tcb=2000.))
    original = bridge.load_stellar_motion_request(live_config)
    bundle = tmp_path/'epoch'
    digest = prepare_stellar_epoch(original, bundle)
    product = load_stellar_epoch(bundle, expected_manifest_sha256=digest)
    event = (TimePoint(original.instant.jd1+1, original.instant.jd2, 'tcb')
             if target == 'reused' else TimePoint(990545, 0., 'tcb'))
    window = 100 if target == 'reused' else 0
    query = tmp_path/'epoch-query.toml'
    query.write_bytes(_epoch_consumer_document(bundle, digest, event, window))
    original_bytes = {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}
    design = configuration_preset_path('b4-portrait', kind='atlas-layout')
    raw = design.read_bytes()
    atlas = AtlasBandTiling.from_json(raw.decode())
    design_digest = sha256(raw).hexdigest()
    sky = _motion_cli_sky(source, live_config.parent)
    class SyntheticSnapshot:
        manifest_sha256 = 'a'*64
        def require(self, **kwargs):
            assert kwargs['design_sha256'] == design_digest
        def make_sky(self):
            return sky
    monkeypatch.setattr(native_snapshot, 'read_native_sky_snapshot',
                        lambda *a, **k: SyntheticSnapshot())
    def forbidden(*a, **k):
        raise AssertionError('Saved native CLI must not create an observer or acquire a source sky')
    monkeypatch.setattr(Observer, '__init__', forbidden)
    monkeypatch.setattr(chart, 'generate_celestial_sphere', forbidden)
    presentation_file = tmp_path/'presentation.toml'
    presentation_file.write_text('schema_version=1\ndocument_kind="wenu-atlas-chart-presentation"\n'
        'layers=["stars","constellation_lines","constellation_labels"]\n'
        'formats=["png","pdf"]\ndpi=36\nlegend_fontsize=6.0\nreport_label_scale=1.0\n')
    presentation = AtlasChartPresentation(
        layers=('stars','constellation_lines','constellation_labels'),
        formats=('png','pdf'), dpi=36, legend_fontsize=6., report_label_scale=1.)
    output = tmp_path/'command'
    arguments = ['atlas-sheet', '--design', str(design), '--config', str(presentation_file),
        '--from-sky', str(tmp_path/'synthetic-snapshot'), '--stellar-epoch-config', str(query),
        '--chart-number', '22', '--output-dir', str(output)]
    assert chart.main(arguments, emit_outputs=False) == 0
    admitted = StellarEpochViewInput(product, event, window)
    request = AtlasSheetChartRequest(atlas.geometry.sheets[21], atlas.geometry.page,
        presentation, tmp_path/'direct', stellar_motion=admitted,
        design_sha256=design_digest, design_bytes=raw)
    generate_chart_request(request, sky=sky)
    for suffix in ('', '_report'):
        name = 'chart-22'+suffix+'.png'
        with Image.open(output/name) as actual, Image.open(request.output_dir/name) as expected:
            np.testing.assert_array_equal(np.asarray(actual), np.asarray(expected))
    report = json.loads((output/'chart-22_report_data.json').read_text())['stellar_realization']
    expected = json.loads((request.output_dir/'chart-22_report_data.json').read_text())['stellar_realization']
    assert report == expected
    receipt = report['epoch_query']
    assert receipt['mode'] == target
    assert receipt['requested_event'] == dict(jd1=event.jd1, jd2=event.jd2, scale='tcb')
    assert receipt['actual_position_event'] == admitted.resolution.receipt()['actual_position_event']
    assert not hasattr(sky.stars, '_stellar_realization')

    # File admission must propagate existing reader/query failures before output.
    invalid = [
        _epoch_consumer_document(bundle, '0'*64, event, window),
        _epoch_consumer_document(bundle, digest, event, -1),
        _epoch_consumer_document(bundle, digest, TimePoint(event.jd1, event.jd2, 'tt'), window),
        _epoch_consumer_document(bundle, digest, TimePoint(-100000000, 0., 'tcb'), 0),
    ]
    for index, document in enumerate(invalid):
        query.write_bytes(document)
        refused = tmp_path/f'refused-{index}'
        command = arguments.copy()
        command[command.index(str(output))] = str(refused)
        assert chart.main(command, emit_outputs=False) == 2
        assert not refused.exists()
    assert original_bytes == {p.name: p.read_bytes() for p in bundle.iterdir() if p.is_file()}

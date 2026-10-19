"""Current planetary nebulae contracts."""

# Contracts consolidated from test_milestone36b_planetary_nebulae.py.
from types import SimpleNamespace

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu.geometry.spherical import SphericalPoints
from wenu.objects.planetary_nebulae import PlanetaryNebulae
from wenu.resources import nonstellar_catalog_path


def observer():
    return SimpleNamespace(
        altaz_frame=AltAz(
            obstime=Time("2026-07-27T02:00:00"),
            location=EarthLocation.from_geodetic(
                lon=-70.65 * u.deg,
                lat=-33.45 * u.deg,
            ),
        )
    )


def test_packaged_planetary_nebula_catalogue_exists():
    path = nonstellar_catalog_path("planetary_nebulae", curated=False)
    assert path.is_file()


def test_catalogue_loads_true_and_probable_objects():
    layer = PlanetaryNebulae(observer())
    table = layer.load(filename=nonstellar_catalog_path('planetary_nebulae', curated=False))
    assert len(table) == 1143
    assert "PN G063.1+13.9" in set(table["identifier"])
    assert "PN G036.1-57.1" in set(table["identifier"])


def test_selection_is_case_insensitive():
    layer = PlanetaryNebulae(observer())
    layer.load()
    geometry = layer.spherical_geometry(
        layer.observer,
        selected=["pn g063.1+13.9"],
    )
    assert geometry.ids.tolist() == ["PN G063.1+13.9"]


def test_geometry_is_one_point_per_object():
    layer = PlanetaryNebulae(
        observer(),
        selected=["PN G063.1+13.9", "PN G036.1-57.1"],
        samples=72,
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 2
    assert np.all(np.isfinite(geometry.lon_deg))
    assert np.all(np.isfinite(geometry.lat_deg))


def test_catalogue_measurements_are_metadata_not_glyph_size():
    layer = PlanetaryNebulae(
        observer(),
        selected=["PN G036.1-57.1"],
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert "major_axis_arcmin" in geometry.metadata
    assert "minor_axis_arcmin" in geometry.metadata
    assert geometry.metadata["geometry_kind"] == "cartographic_symbol"


def test_empty_selection_returns_empty_points():
    layer = PlanetaryNebulae(observer(), selected=["not-an-object"])
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 0


def test_sequential_nebula_selections_share_observed_catalogue():
    layer = PlanetaryNebulae(observer())
    layer.load()

    first = layer.spherical_geometry(
        layer.observer,
        selected=["PN G063.1+13.9"],
    )
    second = layer.spherical_geometry(
        layer.observer,
        selected=["PN G036.1-57.1"],
    )

    assert first.ids.tolist() == ["PN G063.1+13.9"]
    assert second.ids.tolist() == ["PN G036.1-57.1"]
    assert len(layer._observed_point_cache) == 1


def _comparison_tool(monkeypatch):
    import importlib
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'tools'))
    return importlib.import_module('compare_planetary_nebulae')


def test_planetary_comparison_identity_signs_conflicts_and_all_memberships(monkeypatch):
    from astropy.table import Table
    tool = _comparison_tool(monkeypatch)
    source = Table(dict(identifier=['PN G001.0+01.0', 'PN G001.0-01.0'],
        common_name=['NGC 1', 'Abell 2'], pk_name=['PK 1+1 1', 'PK 1-1 1'],
        alternate_names=['A 1', 'shared'], major_axis_arcmin=[1., 2.],
        optical_diameter_limit=['', ''], optical_diameter_uncertain=['', ''],
        log_hbeta_flux=[-12., np.nan]))
    def record(group, *names):
        return dict(catalogue=group, designation=names[0], identifiers=list(names), source_file='synthetic.csv')
    records = [record('messier', 'M 1'), record('caldwell', 'C 1'),
        record('al_planetary_nebulae', 'PK 001-01.1'),
        record('sac_best_ngc', 'NGC 0001', 'shared'), record('sac_urban', 'absent')]
    result, crosswalk, summary = tool.compare(source, records,
        {'m1': ['NGC 1'], 'c1': ['NGC 1']})
    assert len(result) == len(source)
    assert list(result['first_list']) == ['messier', 'al_planetary_nebulae']
    assert result[0]['memberships'] == 'messier|caldwell'
    assert list(result['in_sac_best_ngc']) == [False, False]
    assert list(crosswalk['status']) == ['matched', 'matched', 'matched', 'ambiguous', 'unmatched']
    assert summary['membership_review_rows'] == 2
    assert tool.pn_key('PNG 1.0-1.0') == tool.pn_key('PN G001.0-01.0')
    assert tool.pn_key('PK 001-01.1') == tool.pn_key('PK 1-1 1')
    assert tool.pn_key('PK 1-1 1') != tool.pn_key('PK 1+1 1')
    assert tool.pn_key('Abell 2') == tool.pn_key('A 2')
    assert tool.source_names('NGC 2371-72') == ['NGC 2371-72', 'NGC 2371', 'NGC 2372']
    assert tool.al_identity_names('Pease 1 (In M15)') == ['Pease 1 (In M15)', 'Pease 1']
    assert 'M15' not in tool.al_identity_names('Pease 1 (In M15)')
    assert tool.al_identity_names('NGC 7048 Hubble 9') == ['NGC 7048 Hubble 9', 'NGC 7048', 'Hubble 9']
    assert tool.pn_key('Hubble 6') == tool.pn_key('Hb 6')
    assert list(source['common_name']) == ['NGC 1', 'Abell 2']
    assert 'memberships' not in source.colnames


def test_planetary_comparison_hbeta_area_limits_and_missing_values(monkeypatch):
    from astropy.table import Table
    tool = _comparison_tool(monkeypatch)
    source = Table(dict(identifier=['a', 'b', 'c', 'd'], common_name=['a', 'b', 'c', 'd'],
        pk_name=['']*4, alternate_names=['']*4, major_axis_arcmin=[2., 2., 0., 4.],
        optical_diameter_limit=['', '<', '', ''], optical_diameter_uncertain=[':', '', '', ''],
        log_hbeta_flux=[-12., -12., -12., np.nan]))
    result, _, summary = tool.compare(source, [])
    assert result[0]['radius_arcmin'] == 1.
    assert np.isclose(result[0]['log_hbeta_surface_brightness_proxy'], -12.-np.log10(np.pi*60**2))
    assert list(result['radius_status']) == ['measured', 'diameter_limit', 'missing_or_nonpositive', 'measured']
    assert np.isnan(np.asarray(result['log_hbeta_surface_brightness_proxy'])[1:]).all()
    assert list(result['hbeta_flux_status']) == ['available', 'available', 'available', 'missing']
    assert summary['rows'] == 4


def test_planetary_comparison_al_original_counts_and_checksum_gate(monkeypatch, tmp_path):
    import shutil
    from pathlib import Path
    import pytest
    tool = _comparison_tool(monkeypatch)
    original = Path(__file__).resolve().parents[1]/'src/wenu/data/observing_lists'
    records, evidence = tool.al_records(original)
    assert len(records) == 246
    assert [evidence['files'][filename]['rows'] for _, filename, _ in tool.AL_FILES] == [110, 110, 26]
    assert any('PN G118.8-74.7' in r['identifiers'] for r in records)
    copied = tmp_path/'al_planetary_nebulae'
    shutil.copytree(original/'al_planetary_nebulae', copied)
    path = copied/'al_planetaries_list_v1.xlsx'
    baseline = path.read_bytes()
    path.write_bytes(baseline+b'corrupted')
    assert path.read_bytes() != baseline
    with pytest.raises(ValueError, match='checksum mismatch'):
        tool.al_records(tmp_path)


def test_planetary_comparison_cli_exports_preserves_source_and_refuses_clobber(monkeypatch, tmp_path, capsys):
    import hashlib
    import json
    from pathlib import Path
    import pytest
    from astropy.table import Table
    tool = _comparison_tool(monkeypatch)
    source = Path(__file__).resolve().parents[1]/'src/wenu/data/catalogs/planetary_nebulae/planetary_nebulae_acker_heasarc.ecsv'
    before = source.read_bytes()
    assert tool.main([]) == 0
    assert '--priority' in capsys.readouterr().out
    assert not list(tmp_path.iterdir())
    args = ['--output-directory', str(tmp_path), '--name', 'planetary_review_v1']
    assert tool.main(args) == 0
    summary = json.loads((tmp_path/'planetary_review_v1_summary.json').read_text())
    table = Table.read(tmp_path/'planetary_review_v1_catalogue.ecsv')
    assert len(table) == summary['rows'] == 1143
    assert summary['lists']['messier']['member_rows'] == 4
    assert summary['lists']['caldwell']['member_rows'] == 13
    assert summary['lists']['al_planetary_nebulae']['member_rows'] == 109
    assert summary['lists']['al_planetary_nebulae_south']['ambiguous_records'] == 4
    assert summary['final_visual_selection'] == 'not_adopted'
    assert source.read_bytes() == before
    for name, expected in summary['products'].items():
        assert hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() == expected

    assert set(summary['plots']) == {'flux', 'surface-brightness'}
    with pytest.raises(FileExistsError):
        tool.main(args)
    with pytest.raises(ValueError, match='explicit _vN'):
        tool.main(['--name', 'unversioned'])


def test_planetary_selection_list_union_strict_flux_missing_values_and_public_review(monkeypatch):
    from astropy.table import MaskedColumn, Table
    import pytest
    tool = _comparison_tool(monkeypatch)
    source = Table(dict(identifier=['listed_missing', 'listed_faint', 'bright', 'boundary', 'missing'],
        log_hbeta_flux=[np.nan, -15., -11.99, -12., np.nan],
        log_hbeta_surface_brightness_proxy=[np.nan, -16., -11., -13., np.nan],
        optical_diameter_uncertain=['', '', ':', '', '']))
    source['in_messier'] = [True, False, False, False, False]
    source['in_caldwell'] = MaskedColumn([False, True, True, False, False],
        mask=[False, False, True, False, False])
    annotated, selected, review, summary = tool.select_catalogue(source)
    assert list(annotated['selection_included']) == [True, True, True, False, False]
    assert list(selected['identifier']) == ['listed_missing', 'listed_faint', 'bright']
    assert summary['reference_list'] == 2 and summary['additional_hbeta_only'] == 1
    assert list(review['identifier']) == ['bright', 'listed_faint', 'listed_missing']
    assert review[0]['surface_brightness_quality'] == 'uncertain_diameter'
    assert not any(selected['public_interest'])
    assert set(selected['public_review_status']) == {'unassessed'}
    assert 'selection_included' not in source.colnames
    for invalid in (float('nan'), float('inf'), True):
        with pytest.raises(ValueError, match='threshold must be finite'):
            tool.select_catalogue(source, invalid)


def test_planetary_selected_cli_exports_exact_union_and_ranked_review(monkeypatch, tmp_path):
    import json
    import hashlib
    from astropy.table import Table
    tool = _comparison_tool(monkeypatch)
    # Existing CLI export test owns plot rendering; inspect this new composition seam.
    def synthetic_plot(table, prefix, view, priority, **kwargs):
        for suffix in ('png', 'svg', 'pdf'):
            prefix.with_name(prefix.name+'_radius_hbeta_'+view+'.'+suffix).write_bytes(b'synthetic plot stub')
        return {}
    monkeypatch.setattr(tool, 'plot', synthetic_plot)
    assert tool.main(['--output-directory', str(tmp_path), '--name', 'selected_pn_v1',
        '--write-selected-catalogue']) == 0
    selected = Table.read(tmp_path/'selected_pn_v1_selected.ecsv')
    all_rows = Table.read(tmp_path/'selected_pn_v1_catalogue.ecsv')
    review = Table.read(tmp_path/'selected_pn_v1_public_review.csv', format='ascii.csv')
    summary = json.loads((tmp_path/'selected_pn_v1_summary.json').read_text())
    assert len(selected) == 319 and len(all_rows) == 1143 and len(review) == 319
    assert summary['selection']['reference_list'] == 178
    assert summary['selection']['additional_hbeta_only'] == 141
    assert sum(all_rows['selection_included']) == 319
    assert not any(selected['public_interest'])
    surface = np.asarray(np.ma.filled(review['log_hbeta_surface_brightness_proxy'], np.nan), float)
    assert np.all(np.diff(surface[np.isfinite(surface)]) <= 0)
    for name, expected in summary['products'].items():
        assert hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() == expected

    catalogue = tmp_path/'selected_pn_v1_selected.ecsv'
    installed = tmp_path/'curated'
    selector = tool.promote_catalogue(catalogue, installed, activate=True)
    assert selector.is_symlink() and selector.readlink().as_posix() == catalogue.name
    assert selector.read_bytes() == catalogue.read_bytes()
    assert tool.promote_catalogue(catalogue, installed, activate=True) == selector
    for name in summary['products']:
        assert (installed/name).read_bytes() == (tmp_path/name).read_bytes()
    layer = PlanetaryNebulae(None)
    normalized = layer.load(filename=selector)
    assert len(normalized) == 319 and np.asarray(normalized['selection_included']).all()
    assert not any(normalized['public_interest'])
    from wenu.sky.native_snapshot import _table_records, _table_from_records
    restored = _table_from_records(_table_records(normalized))
    assert list(restored['identifier']) == list(normalized['identifier'])
    assert list(restored['selection_included']) == list(normalized['selection_included'])
    assert list(restored['public_review_status']) == list(normalized['public_review_status'])
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    geometry = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
    assert len(geometry) == 319 and 'selection_reason' in geometry.metadata
    assert not geometry.metadata['public_interest'].any()

    import pytest
    before_catalogue = selector.read_bytes()
    criteria_path = tool.publish_criteria(selector)
    criteria = json.loads(criteria_path.read_text())
    assert criteria_path.parent == installed
    assert criteria['catalogue']['sha256'] == hashlib.sha256(before_catalogue).hexdigest()
    assert len(criteria['pages']) == 3
    assert any('strict' in p for p in criteria['policy'])
    assert selector.read_bytes() == before_catalogue
    with pytest.raises(FileExistsError):
        tool.publish_criteria(selector)
    blocked = tmp_path/'blocked'
    blocked.mkdir()
    (blocked/'planetary_nebulae.ecsv').write_text('preserve regular selector')
    with pytest.raises(ValueError, match='regular file'):
        tool.promote_catalogue(catalogue, blocked, activate=True)
    assert list(blocked.iterdir()) == [blocked/'planetary_nebulae.ecsv']
    review_path = tmp_path/'selected_pn_v1_public_review.csv'
    before = review_path.read_bytes()
    review_path.write_bytes(before+b'corrupted')
    assert review_path.read_bytes() != before
    rejected = tmp_path/'rejected'
    with pytest.raises(ValueError, match='checksum mismatch'):
        tool.promote_catalogue(catalogue, rejected, activate=True)
    assert not rejected.exists()


def test_pn_returned_states_control_native_points_and_warm_observation(tmp_path, monkeypatch):
    from dataclasses import replace
    from astropy.coordinates import SkyCoord
    from astropy.table import Table
    from wenu.catalogue_state import _unit_direction
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    source = Table(dict(identifier=['PN a', 'PN b'], ra_deg=[10., 20.], dec_deg=[-20., -30.],
        major_axis_arcmin=[2., 4.], minor_axis_arcmin=[1., 3.],
        common_name=['synthetic A', 'synthetic B'], log_hbeta_flux=[-12., -13.],
        in_messier=[True, False], public_interest=[False, False]))
    source.meta = dict(catalog='syntheticPN', catalog_version='synthetic-v1',
        documentation_url='https://example.invalid/syntheticPN')
    for name in ('ra_deg', 'dec_deg'):
        source[name].unit = u.deg
    for name in ('major_axis_arcmin', 'minor_axis_arcmin'):
        source[name].unit = u.arcmin
    path = tmp_path/'synthetic.ecsv'; source.write(path)
    resolved = observer(); layer = PlanetaryNebulae(resolved); layer.load(filename=path)
    original = layer.source_catalog.copy(copy_data=True)
    record = layer.require_catalogue_lookup_metadata().to_record()
    selection = ['pn b', 'PN a', 'PN b', 'absent']
    layer.spherical_geometry(resolved, selected=selection)
    layer.spherical_centers(resolved)
    values = {'PN a': (35., -10.), 'PN b': (75., 15.)}
    evaluate, calls = KernelSession.evaluate, []
    def shift(session, query):
        batch = evaluate(session, query); calls.append(batch)
        return replace(batch, states=tuple(replace(state, vector=_unit_direction(
            *values[state.object_key.value.rsplit(':', 1)[-1]])) for state in batch.states))
    monkeypatch.setattr(KernelSession, 'evaluate', shift)
    native = layer.position()
    np.testing.assert_allclose(native.lon_deg, [35., 75.])
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    symbols = layer.realize(context, None, selected=selection)
    assert list(symbols.ids) == ['PN a', 'PN b']  # Native retains catalogue order.
    np.testing.assert_allclose(symbols.lon_deg, [35., 75.])
    filtered = layer.realize(context, None, minimum_size_arcmin=3.)
    assert list(filtered.ids) == ['PN b']
    np.testing.assert_allclose(filtered.lon_deg, [75.])
    points = layer.spherical_centers(resolved)
    expected = SkyCoord(ra=[35., 75.]*u.deg, dec=[-10., 15.]*u.deg).transform_to(resolved.altaz_frame)
    np.testing.assert_allclose(points.lon_deg, expected.az.deg)
    observed = layer.spherical_geometry(resolved, selected=selection)
    assert list(observed.ids) == ['PN b', 'PN a', 'PN b']  # Observed preserves request order/duplicates.
    np.testing.assert_allclose(observed.lon_deg, expected.az.deg[[1, 0, 1]])
    assert observed.metadata['geometry_kind'] == 'cartographic_symbol'
    assert observed.metadata['major_axis_arcmin'].tolist() == [4., 2., 4.]
    assert observed.metadata['in_messier'].tolist() == [False, True, False]
    assert len(calls) == 5
    assert layer.catalogue_metadata.to_record() == record
    for name in original.colnames:
        np.testing.assert_array_equal(original[name], layer.source_catalog[name])
    empty = layer.spherical_geometry(resolved, selected=['absent'])
    assert len(empty) == 0 and len(calls) == 5


@pytest.mark.parametrize('failure', ('kernel', 'lookup'))
def test_packaged_pn_all_routes_refuse_after_warm_symbol_cache(monkeypatch, failure):
    from wenu_kernel import KernelSession
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    resolved = observer(); layer = PlanetaryNebulae(resolved); layer.load()
    record = layer.require_catalogue_lookup_metadata().to_record()
    with pytest.raises(ValueError, match='Incomplete nonstellar metadata'):
        layer.require_complete_metadata()
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    selected = ['PN G063.1+13.9']
    actions = (layer.position, lambda: layer.realize(context, None, selected=selected),
        lambda: layer.spherical_centers(resolved, selected=selected),
        lambda: layer.spherical_geometry(resolved, selected=selected))
    for action in actions:
        action()
    def refuse(*args, **kwargs):
        raise RuntimeError('synthetic PN refusal')
    if failure == 'kernel':
        monkeypatch.setattr(KernelSession, 'evaluate', refuse)
    else:
        monkeypatch.setattr(layer, 'require_catalogue_lookup_metadata', refuse)
    for action in actions:
        with pytest.raises(RuntimeError, match='PN refusal'):
            action()
    assert layer.catalogue_metadata.to_record() == record


def test_pn_lookup_identity_retains_unknown_physical_facts():
    from wenu.catalogue_state import catalogue_direction_states
    from wenu_kernel.records import TimePoint
    layer = PlanetaryNebulae(None); layer.load()
    row = layer.catalog[0]
    rows = ((str(row['identifier']), float(row['ra_deg']), float(row['dec_deg'])),)
    provider = layer._direction_provider(rows, 'tt')
    admission = provider.describe().admissions[0]
    assert 'planetary-nebula' in admission.model.model_id
    assert 'catalogue_lookup' in admission.capabilities
    assert admission.reference.origin_id == 'legacy-unverified-origin'
    states = catalogue_direction_states(provider, TimePoint(0, 0, 'tt'))
    assert len(states) == 1 and states[0].source_epoch is None
    assert layer.catalogue_metadata.to_record()['epoch'] is None

"""Current open clusters contracts."""

# Contracts consolidated from test_milestone37b_open_clusters.py.
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time
from matplotlib.collections import PathCollection
from matplotlib.path import Path

from wenu.charts.styles import PublicationStyle
from wenu.geometry.spherical import SphericalPoints
from wenu.objects.open_clusters import OpenClusters
from wenu.projections import StereographicProjection
from wenu.rendering import MatplotlibRenderer
from wenu.rendering.symbols import DEFAULT_SYMBOLS
from wenu.resources import nonstellar_catalog_path


class _HashableLayer:
    pass


def test_native_cluster_epoch_tracks_selected_rows_and_preserves_source_metadata():
    from astropy.table import Table
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    table = Table(dict(identifier=['new', 'unknown', 'other'], ra_deg=[15., 30., 45.],
        dec_deg=[20., 25., 30.], apparent_diameter_arcmin=[1., 2., 3.],
        object_type=['Open Cluster'] * 3, position_epoch=['J2016.0', 'unknown', 'J2025.0'],
        RA_source=['first', 'legacy', 'second']),
        meta={'database': 'synthetic', 'original': {'source_release': ['v1', 'v2']}})
    layer = OpenClusters(None)
    layer.catalog = table
    all_rows = layer.position()
    assert all_rows.coordinate_spec.epoch is None
    assert all_rows.metadata['position_epoch'].tolist() == ['J2016.0', 'unknown', 'J2025.0']
    assert all_rows.metadata['RA_source'].tolist() == ['first', 'legacy', 'second']
    assert all_rows.metadata['catalogue_metadata'] == table.meta
    all_rows.metadata['catalogue_metadata']['original']['source_release'].append('changed')
    assert table.meta['original']['source_release'] == ['v1', 'v2']
    context = LayerRealizationContext(NATIVE_ICRS_SPEC)
    chosen = layer.realize(context, None, selected=['other', 'new'])
    assert chosen.ids.tolist() == ['other', 'new']
    assert chosen.coordinate_spec.epoch is None
    assert chosen.metadata['position_epoch'].tolist() == ['J2025.0', 'J2016.0']
    for identifier, epoch in (('new', 'J2016.0'), ('unknown', None), ('other', 'J2025.0')):
        layer.selected = [identifier]
        assert layer.position().coordinate_spec.epoch == epoch
    assert layer.realize(context, None, selected=[]).coordinate_spec.epoch is None
    from astropy.table import MaskedColumn
    masked = table.copy(copy_data=True)
    masked['position_epoch'] = MaskedColumn(['J2016.0'] * 3, mask=[False, True, False])
    layer.catalog, layer.selected = masked, None
    assert layer.position().coordinate_spec.epoch is None
    np.testing.assert_array_equal(np.ma.getmaskarray(layer.position().metadata['position_epoch']), [False, True, False])
    assert len(table) == 3


def test_packaged_cluster_geometry_uses_existing_epoch_and_coordinate_source_columns():
    layer = OpenClusters(None)
    table = layer.load()
    before = table.copy(copy_data=True)
    geometry = layer.position()
    assert geometry.coordinate_spec.epoch is None
    np.testing.assert_array_equal(geometry.metadata['position_epoch'], table['position_epoch'])
    np.testing.assert_array_equal(geometry.metadata['RA_source'], table['RA_source'])
    known = table[np.asarray(table['position_epoch']) != 'unknown']
    assert len(known) and len(known) < len(table)
    identifier = str(known['wenu_id'][0])
    layer.selected = [identifier]
    assert layer.position().coordinate_spec.epoch == str(known['position_epoch'][0])
    assert table.meta == before.meta
    for name in table.colnames:
        np.testing.assert_array_equal(np.ma.getmaskarray(table[name]), np.ma.getmaskarray(before[name]))


def test_cluster_epoch_does_not_infer_measurement_date_from_frame_name():
    from astropy.table import Table
    layer = OpenClusters(None)
    layer.catalog = Table(dict(identifier=['constructed'], ra_deg=[15.], dec_deg=[20.]),
                          meta={'coordinate_frame': 'ICRS/J2000'})
    assert layer.position().coordinate_spec.epoch is None
    layer.catalog.meta['coordinate_epoch'] = 'J1985.5'
    assert layer.position().coordinate_spec.epoch == 'J1985.5'


def test_invalid_cluster_epoch_is_refused_before_replacing_active_catalogue(tmp_path):
    import pytest
    from astropy.table import Table
    layer = OpenClusters(None)
    previous = layer.load()
    source = layer.source
    invalid = Table(dict(identifier=['synthetic'], ra_deg=[15.], dec_deg=[20.],
        apparent_diameter_arcmin=[1.], object_type=['Open Cluster'], position_epoch=['invalid']),
        meta={'database': 'synthetic'})
    filename = tmp_path / 'invalid.ecsv'
    invalid.write(filename)
    with pytest.raises(ValueError, match='coordinate epoch'):
        layer.load(filename=filename)
    assert layer.catalog is previous and layer.source == source


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


def test_packaged_open_cluster_catalogue():
    path = nonstellar_catalog_path("open_clusters", curated=False)
    assert path.is_file()
    layer = OpenClusters(observer())
    table = layer.load(filename=path)
    assert len(table) == 1931
    assert "IC 2602" in set(table["identifier"])
    assert "NGC 4755" in set(table["identifier"])
    assert np.count_nonzero(table['excluded_ir_embedded']) == 349
    assert np.count_nonzero(table['amateur_exclusion_reason'] == 'infrared_discovery') == 344
    assert np.count_nonzero(table['amateur_exclusion_reason'] == 'embedded') == 5
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    native = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None,
        exclude_infrared_embedded=True)
    observed = layer.spherical_geometry(layer.observer, exclude_infrared_embedded=True)
    assert len(native) == len(observed) == 1582
    assert len(layer.catalog) == 1931
    assert not np.any(native.metadata['excluded_ir_embedded'])


def test_observing_catalogue_comparison_preserves_dias_and_group_members(tmp_path):
    import importlib.util
    import json
    from pathlib import Path
    from astropy.table import Table
    import pytest
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('compare_open_clusters', root/'tools/compare_open_clusters.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    dias = Table.read(nonstellar_catalog_path('open_clusters', curated=False))
    original = dias.copy(copy_data=True)
    caldwell = Table.read(nonstellar_catalog_path('caldwell'))
    messier = Table.read(nonstellar_catalog_path('messier'))
    annotated, edges, summary = tool.compare(dias, caldwell, messier)
    assert len(annotated) == 1931 and len(edges) == 56
    assert summary['catalogue_component_matches']['Caldwell']['entries'] == 28
    assert summary['catalogue_component_matches']['Caldwell']['matched'] == 29
    assert summary['catalogue_component_matches']['Messier']['matched'] == 27
    for row in dias:
        expected = original[np.flatnonzero(original['identifier'] == row['identifier'])[0]]
        assert row['identifier'] == expected['identifier']
        assert row['ra_deg'] == expected['ra_deg']
    assert dias.colnames == original.colnames
    assert set(edges['dias_identifier'][edges['designation'] == 'C 14']) == {'NGC 869', 'NGC 884'}
    assert list(edges['dias_identifier'][edges['designation'] == 'M 45']) == ['Melotte 22']
    assert list(edges['dias_identifier'][edges['designation'] == 'C 41']) == ['Melotte 25']
    assert 'C 49' not in set(edges['designation'])  # Rosette nebula is not the cluster.
    review = summary['catalogue_component_matches']['Caldwell']['alias_review']
    assert {r['designation'] for r in review} == {'C 37', 'C 50'}
    assert np.count_nonzero(annotated['in_caldwell']) == 29
    assert np.count_nonzero(annotated['in_messier']) == 27
    assert not np.any(annotated['in_caldwell'] & annotated['in_messier'])
    filtered, _, filtered_summary = tool.compare(dias, caldwell, messier, exclude_ir_embedded=True)
    assert len(filtered) == 1931 and np.count_nonzero(filtered['in_amateur_sample']) == 1582
    assert filtered_summary['selection']['marked_ir_embedded'] == 349
    # Inclusive E(B-V) bounds and explicit treatment of unknown reddening.
    synthetic = Table(dict(reddening_e_bv=[.2,.5,.8,np.nan],
        amateur_exclusion_reason=['','','','']))
    keep, reasons = tool.selection_mask(synthetic, np.ones(4,dtype=bool), .5, None, 'exclude')
    assert keep.tolist() == [True,True,False,False]
    assert reasons == ['','','above_max_E_BV','missing_E_BV']
    keep, _ = tool.selection_mask(synthetic, np.ones(4,dtype=bool), .5, None, 'include')
    assert keep.tolist() == [True,True,False,True]
    with pytest.raises(ValueError):
        tool.selection_mask(synthetic, np.ones(4,dtype=bool), .2, .5, 'exclude')
    # A second exact-identifier candidate is an ambiguity, never a first match.
    duplicate = dias.copy(copy_data=True)
    duplicate.add_row(dias[np.flatnonzero(dias['identifier'] == 'NGC 869')[0]])
    assert len(duplicate) == len(dias)+1
    _, bad_edges, bad_summary = tool.compare(duplicate, caldwell, messier)
    assert len(bad_summary['catalogue_component_matches']['Caldwell']['ambiguous']) == 1
    assert list(bad_edges['status'][bad_edges['component'] == 'NGC0869']) == ['ambiguous']
    prefix = tmp_path/'comparison_v1'
    assert tool.main(['--output-prefix', str(prefix), '--x', 'diameter', '--y', 'brightness',
        '--max-ebv', '.5', '--write-filtered-catalogue']) == 0
    emitted = json.loads((tmp_path/'comparison_v1_summary.json').read_text())
    assert emitted['dias_clusters'] == 1931 and len(emitted['source_sha256']) == 3
    retained = Table.read(tmp_path/'comparison_v1_filtered.ecsv')
    assert len(retained) == emitted['selection']['eligible']
    assert np.all(np.asarray(retained['reddening_e_bv']) <= .5)
    assert not np.any(retained['excluded_ir_embedded'])
    availability = emitted['plot_parameter_availability']
    assert sum(availability[key] for key in ('both','missing_y','missing_x','missing_both')) == len(retained)
    assert availability['x'] == 'diameter' and availability['y'] == 'brightness'
    assert (tmp_path/'comparison_v1_figure.png').exists()
    assert (tmp_path/'comparison_v1_figure.svg').exists()
    assert (tmp_path/'comparison_v1_figure.pdf').exists()
    with pytest.raises(FileExistsError):
        tool.main(['--output-prefix', str(prefix)])


def test_requested_order_and_metadata_are_preserved():
    layer = OpenClusters(
        observer(),
        selected=["NGC 4755", "IC 2602"],
    )
    layer.load(filename=nonstellar_catalog_path('open_clusters', curated=False))
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert geometry.ids.tolist() == ["NGC 4755", "IC 2602"]
    assert geometry.metadata["symbol"] == "open_cluster"
    assert "apparent_diameter_arcmin" in geometry.metadata


def test_open_cluster_photometry_rejects_ambiguous_and_noncluster_matches():
    import importlib.util
    from pathlib import Path
    from astropy.table import Table
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('compare_open_clusters', root/'tools/compare_open_clusters.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    def row(kind, aliases='', ngc=''):
        return dict(Type=kind, Identifiers=aliases, NGC=ngc, IC='', Sources='V-Mag:2',
            **{'V-Mag':'5.0', 'OpenNGC notes':'', 'NED notes':''})
    sources = {'NGC0001': ('NGC.csv', row('OCl','shared alias')),
               'NGC0002': ('NGC.csv', row('OCl','shared alias')),
               'NGC0003': ('NGC.csv', row('G')),
               'NGC0004': ('NGC.csv', row('Dup', ngc='1'))}
    dias = Table(dict(identifier=['NGC 1','shared alias','NGC 3','NGC 4']))
    table = tool.openngc_photometry(dias, sources)
    assert list(table['photometry_status']) == ['measured_V','ambiguous','type_conflict','measured_V']
    assert np.isnan(table['v_magnitude'][1:3]).all()
    assert list(table['photometry_identity_review']) == [True,False,False,True]
    assert list(table['identifier']) == list(dias['identifier'])


def test_open_cluster_coordinates_are_vectorized_and_finite():
    layer = OpenClusters(
        observer(),
        selected=["IC 2391", "NGC 3532", "NGC 2516"],
    )
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert len(geometry) == 3
    assert np.all(np.isfinite(geometry.lon_deg))
    assert np.all(np.isfinite(geometry.lat_deg))


def test_empty_selection_returns_empty_points():
    layer = OpenClusters(observer(), selected=["not-a-cluster"])
    layer.load()
    geometry = layer.spherical_geometry(layer.observer)
    assert isinstance(geometry, SphericalPoints)
    assert len(geometry) == 0


def test_sequential_open_cluster_selections_share_observed_catalogue():
    layer = OpenClusters(observer())
    layer.load(filename=nonstellar_catalog_path('open_clusters', curated=False))

    first = layer.spherical_geometry(
        layer.observer,
        selected=["IC 2602"],
    )
    second = layer.spherical_geometry(
        layer.observer,
        selected=["NGC 4755"],
    )

    assert first.ids.tolist() == ["IC 2602"]
    assert second.ids.tolist() == ["NGC 4755"]
    assert len(layer._observed_point_cache) == 1


def test_open_cluster_symbol_is_dotted_circumference():
    marker = DEFAULT_SYMBOLS.open_cluster
    assert isinstance(marker, Path)
    assert np.max(np.abs(marker.vertices)) <= 1.0
    assert np.count_nonzero(marker.codes == Path.MOVETO) == 12


def test_publication_style_uses_symbol_library_and_optional_labels():
    layer = _HashableLayer()
    sky = SimpleNamespace(
        stars=None,
        nonstellar=None,
        milky_way_isophotes=None,
        magellanic_cloud_isophotes={},
        galaxies=None,
        supernova_remnants=None,
        planetary_nebulae=None,
        globular_clusters=None,
        open_clusters=layer,
        constellation_lines=None,
        constellation_labels=None,
        constellation_boundaries=None,
        points=None,
        layers=(layer,),
    )
    style = PublicationStyle(open_cluster_symbol_size=81.0)
    render = style.layer_options(sky)[layer]["render"]
    assert render["style"]["marker"] is DEFAULT_SYMBOLS.open_cluster
    assert render["style"]["s"] == 81.0
    assert render["draw_labels"] is False


def test_selected_clusters_render_as_one_path_collection():
    layer = OpenClusters(
        observer(),
        selected=["IC 2602", "NGC 4755"],
    )
    layer.load()
    spherical = layer.spherical_geometry(layer.observer)
    projected = StereographicProjection().project_geometry(spherical)
    fig, ax = plt.subplots()
    artists = MatplotlibRenderer(ax).draw(
        projected,
        style={
            "marker": DEFAULT_SYMBOLS.open_cluster,
            "s": 64.0,
            "facecolors": "white",
            "edgecolors": "white",
        },
    )
    assert len(artists) == 1
    assert isinstance(artists[0], PathCollection)
    assert len(artists[0].get_offsets()) == 2
    plt.close(fig)



def test_hunt_member_photometry_rank_policy_and_help(tmp_path, capsys):
    import importlib.util
    from pathlib import Path
    from astropy.table import Table
    import pytest
    root = Path(__file__).resolve().parents[1]
    def tool(name):
        spec = importlib.util.spec_from_file_location(name, root/'tools'/f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    hunt = tool('hunt_reffert_catalogue')
    compare = tool('compare_open_clusters')
    assert compare.main([]) == 0
    help_text = capsys.readouterr().out
    assert '--catalogue' in help_text and 'hunt-curated' in help_text and 'v5' in help_text and '--max-v10' in help_text
    assert not list(tmp_path.iterdir())
    with pytest.raises(SystemExit):
        compare.main(['--catalogue','dias','--y','v5'])
    with pytest.raises(SystemExit):
        compare.main(['--catalogue','dias','--max-v10','11'])
    # Synthetic fixture: policy boundary, reversed V/G ordering, exact IDs,
    # missing colours, no extrapolation, and observed (not dereddened) sums.
    clusters = Table(dict(hunt_id=[1,2], identifier=['synthetic A','synthetic B']))
    stars = [dict(hunt_id=1,source_id=str(6000000000000000000+i),probability=.5,
        inrt=1,inrj=1,g=9+i*.2,bp=10+i*.2,rp=9+i*.2) for i in range(6)]
    stars[0].update(bp=13.,rp=9.)  # G brightest, V fainter than fifth.
    stars += [dict(hunt_id=1,source_id='7',probability=.49,inrt=1,inrj=1,g=1.,bp=2.,rp=1.),
              dict(hunt_id=1,source_id='8',probability=1.,inrt=0,inrj=0,g=2.,bp=3.,rp=2.),
              dict(hunt_id=1,source_id='9',probability=1.,inrt=1,inrj=1,g=10.,bp=np.nan,rp=9.)]
    result = hunt.member_statistics(clusters,iter(stars))
    assert result['accepted_member_count'][0] == 7
    assert result['g5_source_id'][0] != result['v5_source_id'][0]
    assert result['v5_source_id'][0] == str(6000000000000000005)
    assert result['missing_v_members'][0] == 1
    assert result['v5_status'][0] == 'partial_photometry'
    assert np.isnan(result['v5'][1]) and result['v5_status'][1] == 'fewer_than_five_valid_V'
    expected_v = 10.-(-.02704+.01424-.2156+.01426)
    assert result['v5'][0] == pytest.approx(expected_v)
    assert hunt.gaia_to_bvr([10],[11],[10])['V'][0] == pytest.approx(expected_v)
    assert np.isnan(hunt.gaia_to_bvr([10],[15],[10])['V'][0])
    assert np.isnan(hunt.gaia_to_bvr([10],[13],[10])['R'][0])
    assert np.isnan(hunt.gaia_to_bvr([10],[13],[10])['B'][0])
    v = hunt.gaia_to_bvr([s['g'] for s in stars[:6]],
        [s['bp'] for s in stars[:6]],[s['rp'] for s in stars[:6]])['V']
    assert result['v_integrated'][0] == pytest.approx(-2.5*np.log10(np.sum(10**(-.4*v))))
    with pytest.raises(ValueError,match='Duplicate'):
        hunt.member_statistics(clusters,iter(stars+[stars[0]]))
    with pytest.raises(ValueError):
        hunt.member_statistics(clusters,iter(stars),minimum_probability=1.1)


def test_hunt_catalogue_plot_selection_export_and_digest(tmp_path):
    import importlib.util
    import hashlib
    import json
    import shutil
    from pathlib import Path
    from astropy.table import Table
    import pytest
    root = Path(__file__).resolve().parents[1]
    def load_tool(name):
        spec = importlib.util.spec_from_file_location(name,root/'tools'/f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    hunt = load_tool('hunt_reffert_catalogue')
    tool = load_tool('compare_open_clusters')
    data = tmp_path/'data'
    for category in ('open_clusters','caldwell','messier'):
        (data/category).mkdir(parents=True)
        source = Path(nonstellar_catalog_path(category, curated=False))
        shutil.copyfile(source,data/category/source.name)
    # Synthetic normalized resource, explicitly not a captured provider fixture.
    rows = Table(dict(identifier=['NGC_869','NGC_884','NGC_2168','synthetic moving group'],
        hunt_id=[1,2,3,4],aliases=['NGC0869','NGC0884','NGC2168',''],hunt_type=['o','o','o','m'],
        source_type_flag=['','','',''],apparent_diameter_arcmin=[20.,20.,30.,40.],
        distance_pc=[100.,100.,200.,300.],reddening_e_bv=[.2,.2,.2,.2],
        log_age_years=[7.,7.,7.,7.],member_count=[10,10,10,10],metallicity_feh=[np.nan]*4,
        v5=[10.999,11.,np.nan,9.],v10=[11.999,12.,np.nan,9.],g5=[10.,10.,np.nan,8.],v_magnitude=[7.,7.,np.nan,6.]))
    rows.meta.update(member_policy=dict(minimum_probability=.5,aperture='tidal'),
        synthetic_fixture=True)
    full = data/'open_clusters'/hunt.FULL_NAME
    curated = data/'open_clusters'/hunt.CURATED_NAME
    rows.write(full,format='ascii.ecsv')
    rows[:1].write(curated,format='ascii.ecsv')
    provenance = dict(files={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        for p in (full,curated)},synthetic_fixture=True)
    (data/'open_clusters'/hunt.PROVENANCE_NAME).write_text(json.dumps(provenance))
    assert tool.identifier_key('NGC_0188') == tool.identifier_key('NGC 188')
    assert tool.identifier_key('Melotte_25') == tool.identifier_key('Melotte 25')
    original_labels = dict(tool.PARAMETERS)
    prefix = tmp_path/'hunt_test_v1'
    arguments = ['--catalogue','hunt-reffert2024','--data-directory',str(data),
        '--output-prefix',str(prefix),'--x','diameter','--y','v5','--max-v5','11',
        '--write-filtered-catalogue']
    assert tool.main(arguments) == 0
    assert tool.PARAMETERS == original_labels
    selected = Table.read(tmp_path/'hunt_test_v1_filtered.ecsv')
    assert list(selected['identifier']) == ['NGC_869']
    all_rows = Table.read(tmp_path/'hunt_test_v1_hunt.csv')
    assert len(all_rows) == 4
    summary = json.loads((tmp_path/'hunt_test_v1_summary.json').read_text())
    assert summary['selection']['eligible'] == 1
    assert summary['samples']['Hunt & Reffert 2024']['clusters'] == 1
    assert summary['samples']['Caldwell']['clusters'] == 1
    assert summary['samples']['Messier']['clusters'] == 0
    assert 'source_identifier' in Table.read(tmp_path/'hunt_test_v1_crosswalk.csv').colnames
    assert (tmp_path/'hunt_test_v1_figure.png').is_file()
    with pytest.raises(FileExistsError):
        tool.main(arguments)
    assert tool.main(['--catalogue','hunt-curated','--data-directory',str(data),
        '--output-prefix',str(tmp_path/'curated_test_v1'),'--y','v5']) == 0
    assert tool.main(['--catalogue','hunt-reffert2024','--data-directory',str(data),
        '--output-prefix',str(tmp_path/'v10_test_v1'),'--y','v10','--max-v10','12',
        '--write-filtered-catalogue']) == 0
    v10_selected = Table.read(tmp_path/'v10_test_v1_filtered.ecsv')
    assert list(v10_selected['identifier']) == ['NGC_869']
    assert v10_selected.meta['selection']['max_v10'] == 12
    assert v10_selected.meta['selection']['max_v5'] is None
    v10_all = Table.read(tmp_path/'v10_test_v1_hunt.csv')
    assert v10_all['selection_exclusion_reason'][1] == 'V10_not_brighter_than_limit'
    assert v10_all['selection_exclusion_reason'][2] == 'missing_V10'
    with pytest.raises(ValueError,match='--max-v10 must be finite'):
        tool.main(['--catalogue','hunt-reffert2024','--data-directory',str(data),
            '--output-prefix',str(tmp_path/'invalid_v10_v1'),'--max-v10','nan'])
    full.write_text(full.read_text()+'\n')
    assert hashlib.sha256(full.read_bytes()).hexdigest() != provenance['files'][full.name]['sha256']
    with pytest.raises(ValueError,match='digest'):
        hunt.load(data/'open_clusters')


def test_hunt_acquisition_receipt_and_no_argument_help(tmp_path, monkeypatch, capsys):
    import gzip
    import hashlib
    import importlib.util
    import io
    import json
    from pathlib import Path
    import pytest
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root/'tools'))
    spec = importlib.util.spec_from_file_location('query_hunt_reffert2024',root/'tools/query_hunt_reffert2024.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    assert tool.main([]) == 0
    assert '--source-directory' in capsys.readouterr().out
    calls = []
    payloads = {name: b'synthetic ReadMe\n' if name == 'ReadMe' else gzip.compress(b'synthetic record\n')
                for name in tool.FILES}
    class Response(io.BytesIO):
        status = 200
    def response(request,timeout):
        calls.append(request.full_url)
        return Response(payloads[request.full_url.rsplit('/',1)[-1]])
    monkeypatch.setattr(tool.urllib.request,'urlopen',response)
    cache = tmp_path/'cache'
    tool.acquire(cache)
    receipt = json.loads((cache/'receipt.json').read_text())
    assert calls == [tool.BASE_URL+name for name in tool.FILES]
    assert all(receipt[name]['sha256'] == hashlib.sha256(payloads[name]).hexdigest() for name in tool.FILES)
    assert not list(cache.glob('*.partial'))
    with pytest.raises(FileExistsError):
        tool.acquire(cache)
    def failure(request,timeout):
        calls.append(request.full_url)
        raise TimeoutError('synthetic transport failure')
    monkeypatch.setattr(tool.urllib.request,'urlopen',failure)
    previous_calls = len(calls)
    failed_cache = tmp_path/'failed'
    with pytest.raises(TimeoutError):
        tool.acquire(failed_cache)
    assert len(calls) == previous_calls+1  # no retry
    assert not (failed_cache/'receipt.json').exists()


def test_packaged_hunt_crosswalk_and_fifth_member_resource():
    import importlib.util
    from pathlib import Path
    from astropy.table import Table
    root = Path(__file__).resolve().parents[1]
    def load_tool(name):
        spec = importlib.util.spec_from_file_location(name,root/'tools'/f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    hunt = load_tool('hunt_reffert_catalogue')
    tool = load_tool('compare_open_clusters')
    directory = root/'src/wenu/data/catalogs/open_clusters'
    full, provenance, _ = hunt.load(directory)
    curated, _, _ = hunt.load(directory,curated=True)
    assert len(full) == 7167 and len(curated) == provenance['curated_rows'] == 431
    assert provenance['source_member_rows'] == 1291929
    assert np.all(np.asarray(curated['hunt_type']) == 'o')
    assert np.all(np.asarray(curated['v5'],float) < 11)
    assert list(curated['identifier']) == list(full['identifier'][full['curated_v5lt11']])
    annotated, edges, summary = tool.compare(full,
        Table.read(nonstellar_catalog_path('caldwell')),
        Table.read(nonstellar_catalog_path('messier')),catalogue_name='Hunt & Reffert 2024')
    assert summary['catalogue_component_matches']['Caldwell']['matched'] == 29
    assert summary['catalogue_component_matches']['Messier']['matched'] == 27
    # Primary Melotte_25 wins over the separate CWNU_1242 alias claim.
    hyades = edges[edges['designation'] == 'C 41'][0]
    assert hyades['dias_identifier'] == 'Melotte_25'
    assert hyades['match_method'] == 'exact_identifier'
    assert hyades['other_alias_rows'] == 'CWNU_1242'
    bright = np.asarray(annotated['v5'],float) < 11
    assert np.count_nonzero(bright & np.asarray(annotated['in_caldwell'])) == 22
    assert np.count_nonzero(bright & np.asarray(annotated['in_messier'])) == 23
    lost = annotated[np.asarray(annotated['in_messier']) & ~bright]
    assert set(lost['messier_designations']) == {'M 11','M 26','M 29','M 103'}


def _union_tool_and_sources(monkeypatch):
    import importlib.util
    from pathlib import Path
    from astropy.table import Table
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root/'tools'))
    spec = importlib.util.spec_from_file_location('merge_open_clusters',root/'tools/merge_open_clusters.py')
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    dias = Table(dict(identifier=['NGC 869','NGC 884','Shared alias','Infrared X'],
        ra_deg=[1.,2.,3.,4.],dec_deg=[10.,20.,30.,40.],
        member_count=[10,20,30,40],source_type_flag=['','','','IR']))
    dias['ra_deg'].unit = 'deg'
    dias['apparent_diameter_arcmin'] = [30.,30.,30.,30.]
    dias['apparent_diameter_arcmin'].unit = 'arcmin'
    dias.meta['coordinate_frame'] = 'ICRS/J2000 as supplied'
    hunt = Table(dict(identifier=['NGC_869','NGC_884','Melotte_22'],hunt_id=[1,2,3],
        aliases=['NGC_869,Shared alias','NGC_884,Shared alias','Melotte_22'],
        ra_deg=[1.1,2.1,5.],dec_deg=[10.1,20.1,50.],hunt_type=['g','m','o'],
        v5=[9.,10.,np.nan]))
    hunt.meta['coordinate_epoch'] = 'J2016.0'
    hunt['apparent_diameter_arcmin'] = [30.,30.,30.]
    hunt['apparent_diameter_arcmin'].unit = 'arcmin'
    caldwell = Table(dict(name=['C 14'],membership_type=['open_cluster_group'],
        cluster_components=['NGC0869|NGC0884'],related_aliases=[''],primary_id=['NGC0869']))
    messier = Table(dict(name=['M 45'],object_type=['OC'],alt_name=['']))
    return tool,dias,hunt,caldwell,messier


def test_open_cluster_union_preserves_rows_parameters_ids_and_compound_references(monkeypatch):
    tool,dias,hunt,caldwell,messier = _union_tool_and_sources(monkeypatch)
    original_dias = dias.copy(copy_data=True)
    original_hunt = hunt.copy(copy_data=True)
    union,edges,refs,registry,summary = tool.merge_catalogues(dias,hunt,caldwell,messier)
    assert len(union)==5 and summary['matched_pairs']==2
    assert sum(union['has_dias'])==4 and sum(union['has_hunt'])==3
    assert len(set(union['wenu_id']))==len(union)
    assert union.colnames[:4]==['wenu_id','RA','Dec','dias_id']
    assert union['RA'].unit==u.deg and union['dias_ra_deg'].unit==u.deg
    assert np.count_nonzero(union['Caldwell_id']=='C 14')==2
    assert np.count_nonzero(union['Messier_id']=='M 45')==1
    paired = union[union['dias_id']=='NGC 869'][0]
    assert paired['RA']==1.1 and paired['dias_ra_deg']==1. and paired['hunt_ra_deg']==1.1
    assert paired['hunt_type']=='g'  # all source classes retained, without curation
    assert paired['NGC_id']=='NGC 869'
    infrared = union[union['dias_id']=='Infrared X'][0]
    assert infrared['dias_source_type_flag']=='IR' and not infrared['has_hunt']
    assert np.ma.is_masked(infrared['hunt_v5'])
    assert np.count_nonzero(edges['status']=='review')==2
    assert union[union['dias_id']=='Shared alias']['identity_review'][0]
    # Pure compilation never mutates source tables or their parameters.
    assert dias.colnames==original_dias.colnames and hunt.colnames==original_hunt.colnames
    np.testing.assert_equal(dias['ra_deg'],original_dias['ra_deg'])
    np.testing.assert_equal(hunt['v5'],original_hunt['v5'])
    reordered,_,_,again,_ = tool.merge_catalogues(dias[::-1],hunt[::-1],caldwell,messier,registry=registry)
    assert again==registry
    assert set(reordered['wenu_id'])==set(union['wenu_id'])
    extended = dias.copy(copy_data=True)
    extended.add_row(dict(identifier='AAA new',ra_deg=0.,dec_deg=0.,member_count=1,source_type_flag='',apparent_diameter_arcmin=30.))
    _,_,_,extended_registry,_ = tool.merge_catalogues(extended,hunt,caldwell,messier,registry=registry)
    assert all(extended_registry['source_ids'][k]==v for k,v in registry['source_ids'].items())
    assert extended_registry['next_id']==registry['next_id']+1


def test_open_cluster_union_registry_conflicts_fail_closed(monkeypatch):
    import pytest
    tool,dias,hunt,caldwell,messier = _union_tool_and_sources(monkeypatch)
    conflict = dict(schema_version=1,next_id=3,source_ids={
        'dias:ngc869':'WOC00000001','hunt:1':'WOC00000002'})
    with pytest.raises(ValueError,match='combines existing Wenu IDs'):
        tool.merge_catalogues(dias,hunt,caldwell,messier,registry=conflict)
    split = dict(schema_version=1,next_id=2,source_ids={
        'dias:infraredx':'WOC00000001','hunt:3':'WOC00000001'})
    with pytest.raises(ValueError,match='split across rows'):
        tool.merge_catalogues(dias,hunt,caldwell,messier,registry=split)
    duplicate = dias.copy(copy_data=True)
    duplicate.add_row(dias[0])
    assert len(duplicate)==len(dias)+1
    with pytest.raises(ValueError,match='Duplicate source identities'):
        tool.merge_catalogues(duplicate,hunt,caldwell,messier)


def test_open_cluster_union_cli_help_export_and_overwrite_policy(tmp_path,monkeypatch,capsys):
    import hashlib
    import json
    import pytest
    from astropy.table import Table
    tool,dias,hunt,caldwell,messier = _union_tool_and_sources(monkeypatch)
    assert tool.main([])==0
    help_text = capsys.readouterr().out
    assert '--id-registry' in help_text and 'wenu_id, RA, Dec' in help_text
    assert '--hunt-diameter-column' in help_text and 'separation < BOTH radii' in help_text
    assert not list(tmp_path.iterdir())
    data = tmp_path/'data'
    for category,filename,table in [
        ('open_clusters','dias.ecsv',dias),('open_clusters','hunt.ecsv',hunt),
        ('caldwell','caldwell_openngc.ecsv',caldwell),('messier','messier_heasarc.ecsv',messier)]:
        (data/category).mkdir(parents=True,exist_ok=True)
        table.write(data/category/filename,format='ascii.ecsv')
    output = tmp_path/'candidate'
    arguments = ['--data-directory',str(data),'--dias-catalogue',str(data/'open_clusters/dias.ecsv'),
        '--hunt-catalogue',str(data/'open_clusters/hunt.ecsv'),'--output-directory',str(output),
        '--name','wenu_open_clusters_v1','--without-observing-lists']
    assert tool.main(arguments)==0
    catalogue = Table.read(output/'wenu_open_clusters_v1.ecsv')
    assert len(catalogue)==5 and catalogue.meta['curation_status']=='unreviewed_candidate'
    assert catalogue.meta['source_sha256']['dias']==hashlib.sha256((data/'open_clusters/dias.ecsv').read_bytes()).hexdigest()
    for name in ['_crosswalk.csv','_references.csv','_positions.csv','_ids.json','_summary.json']:
        assert (output/('wenu_open_clusters_v1'+name)).exists()
    receipt = json.loads((output/'wenu_open_clusters_v1_summary.json').read_text())
    assert receipt['dias_rows']==4 and receipt['hunt_rows']==3
    assert receipt['positional_audit']['identifier_matched']['pass_count']==2
    assert receipt['observing_membership']['status']=='explicitly_skipped'
    assert np.all(catalogue['in_al_open_clusters'].mask)
    assert all(hashlib.sha256((output/name).read_bytes()).hexdigest()==value for name,value in receipt['products'].items())
    with pytest.raises(FileExistsError):
        tool.main(arguments)
    with pytest.raises(SystemExit):
        tool.main(['--name','unversioned'])


def test_open_cluster_positional_audit_counts_pairs_and_unique_unmatched_objects(monkeypatch):
    import pytest
    from astropy.table import Table
    tool,*_ = _union_tool_and_sources(monkeypatch)
    dias = Table(dict(identifier=['A','B','C','D','E'],
        ra_deg=[359.99,10.,20.,90.,0.],dec_deg=[0.]*5,
        apparent_diameter_arcmin=[4.,6.,np.nan,6.,4.]))
    hunt = Table(dict(identifier=['A','B','C','X','Y'],hunt_id=[1,2,3,4,5],
        ra_deg=[.01,10.1,20.,90.01,90.02],dec_deg=[0.]*5,
        apparent_diameter_arcmin=[4.,20.,4.,6.,6.]))
    groups,_ = tool.identify(dias,hunt)
    ledger,counts = tool.positional_audit(dias,hunt,groups)
    assert counts['identifier_matched_pairs']==3
    assert counts['identifier_matched']==dict(pass_count=1,fail_count=1,unassessable_count=1)
    assert counts['passing_candidates']['both_unmatched']==dict(pairs=2,distinct_dias=1,distinct_hunt=2)
    assert counts['passing_candidates']['matched_elsewhere']==dict(pairs=1,distinct_dias=1,distinct_hunt=1)
    assert counts['nonidentified_passing_pairs']==3
    assert counts['nonidentified_distinct_dias']==2 and counts['nonidentified_distinct_hunt']==3
    assert counts['invalid_or_missing']['dias']['radius']==1
    assert len(ledger)==6
    matched = ledger[ledger['identifier_matched']]
    assert list(matched['positional_status'])==['pass','fail','unassessable']
    assert matched['separation_arcmin'][0]==pytest.approx(1.2)
    # The B pair is inside the Hunt radius, but outside the Dias radius.
    assert matched['dias_radius_arcmin'][1] < matched['separation_arcmin'][1] < matched['hunt_radius_arcmin'][1]
    assert ledger['separation_arcmin'].unit==u.arcmin
    assert tool.identify(dias,hunt)[0]==groups


def test_open_cluster_positional_audit_spherical_units_boundary_and_missing(monkeypatch):
    import pytest
    from astropy.table import Table, MaskedColumn
    tool,*_ = _union_tool_and_sources(monkeypatch)
    dias = Table(dict(identifier=['P'],ra_deg=[0.],dec_deg=[89.],diameter=[5.]))
    hunt = Table(dict(identifier=['P'],hunt_id=[1],ra_deg=[180.],dec_deg=[89.],diameter=[5.]))
    dias['diameter'].unit = hunt['diameter'].unit = u.deg
    groups,_ = tool.identify(dias,hunt)
    kwargs = dict(dias_diameter_column='diameter',hunt_diameter_column='diameter')
    ledger,counts = tool.positional_audit(dias,hunt,groups,**kwargs)
    assert ledger['separation_arcmin'][0]==pytest.approx(120.)
    assert counts['identifier_matched']['pass_count']==1
    # Exact boundary is excluded by the strict criterion.
    dias['diameter'][0] = ledger['separation_arcmin'][0]/30
    _,counts = tool.positional_audit(dias,hunt,groups,**kwargs)
    assert counts['identifier_matched']['fail_count']==1
    hunt['diameter'] = MaskedColumn([5.],mask=[True],unit=u.deg)
    _,counts = tool.positional_audit(dias,hunt,groups,**kwargs)
    assert counts['identifier_matched']['unassessable_count']==1
    hunt['dec_deg'][0] = 91.
    _,counts = tool.positional_audit(dias,hunt,groups,**kwargs)
    assert counts['invalid_or_missing']['hunt']['coordinates']==1
    with pytest.raises(ValueError,match='lacks column'):
        tool.positional_audit(dias,hunt,groups)


def test_observing_membership_uses_names_preserves_compounds_and_masks_conflicts(monkeypatch):
    from astropy.table import Table
    _union_tool_and_sources(monkeypatch)
    import observing_list_membership as lists
    table = Table(dict(wenu_id=['W1','W2','W3','W4'],
        dias_id=['NGC 869','NGC 884','Berk 58','Different'],
        hunt_name=['NGC_869','NGC_884','Berkeley_58','Different'],
        Other_ids=['NGC 869|Shared','NGC 884|Shared','Berkeley 58','NGC 869'],
        Messier_id=['','','M 45',''],Caldwell_id=['C 14','C 14','','']))
    def record(cat,name,ids):return dict(catalogue=cat,designation=name,identifiers=ids,source_file='synthetic.csv')
    records=[record('caldwell','C 14',['C 14']),record('messier','M 45',['M 45']),
             record('al_open_clusters','Berk 58',['Berk 58']),
             record('sac_best_ngc','NGC 869',['NGC 869']),
             record('herschel2','Shared',['Shared'])]
    edges,summary = lists.annotate(table,records)
    assert list(table['in_caldwell'])==[True,True,False,False]
    assert table['in_messier'][2] and table['in_al_open_clusters'][2]
    assert table['in_sac_best_ngc'][0] and np.ma.is_masked(table['in_sac_best_ngc'][3])
    assert np.ma.is_masked(table['in_herschel2'][0]) and np.ma.is_masked(table['in_herschel2'][1])
    np.testing.assert_equal(table['in_best_ngc'],table['in_sac_best_ngc'])
    assert summary['counts']['al_open_clusters']['member_rows']==1
    assert edges[edges['catalogue']=='caldwell']['wenu_ids'][0]=='W1|W2'
    assert list(table['dias_id'])==['NGC 869','NGC 884','Berk 58','Different']
    assert lists.key('Cr 140')==lists.key('Collinder_140')
    assert lists.key('Ru 1')==lists.key('Ruprecht_1')
    unresolved=table.copy(copy_data=True)
    unresolved['Caldwell_id']=['']*len(table)
    reference_edges=Table(dict(catalogue=['Caldwell'],designation=['C 14'],
        status=['ambiguous'],candidate_identifiers=['NGC 869|NGC 884'],other_alias_rows=['']))
    lists.annotate(unresolved,records,reference_edges=reference_edges)
    assert np.ma.is_masked(unresolved['in_caldwell'][0])
    assert np.ma.is_masked(unresolved['in_caldwell'][1])


def test_first_pass_xlsx_preserves_blank_rows_and_stored_cells(tmp_path,monkeypatch):
    from zipfile import ZipFile
    _union_tool_and_sources(monkeypatch)
    import observing_list_membership as lists
    path=tmp_path/'tiny.xlsx'
    with ZipFile(path,'w') as archive:
        archive.writestr('xl/sharedStrings.xml','<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><si><t>Berk 58</t></si></sst>')
        archive.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c></row><row r="3"><c r="B3" t="inlineStr"><is><t>source text</t></is></c><c r="C3"><v>9.7</v></c></row></sheetData></worksheet>')
    assert lists.xlsx_rows(path)==[[['Berk 58'],[],['','source text','9.7']]]


def test_converted_membership_hash_validation_and_converter_help(tmp_path,monkeypatch,capsys):
    import csv,hashlib,json,pytest
    _union_tool_and_sources(monkeypatch)
    import observing_list_membership as lists
    import convert_observing_catalogues as converter
    assert converter.main([])==0
    assert '--source-directory' in capsys.readouterr().out
    assert not list(tmp_path.iterdir())
    registry=tmp_path/'registry.json'
    source_rows=[dict(file=name,sha256='0'*64) for name in lists.SOURCE_FILES]
    registry.write_text(json.dumps(dict(products=source_rows)))
    directory=tmp_path/'csv_v1';directory.mkdir()
    index=directory/'observing_memberships_v1.csv'
    with index.open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['catalogue','designation','identifiers_json','source_file'])
        for name,count in lists.SOURCE_COUNTS.items():
            for i in range(count):writer.writerow([name,str(i),json.dumps(['NGC '+str(i)]),lists.SOURCE_FILES[0]])
    receipt=dict(source_registry_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
        source_sha256={r['file']:r['sha256'] for r in source_rows},
        products=[dict(file=index.name,bytes=index.stat().st_size,sha256=hashlib.sha256(index.read_bytes()).hexdigest())])
    (directory/'conversion_receipt_v1.json').write_text(json.dumps(receipt))
    records,_=lists.load_converted(directory,registry)
    assert len(records)==sum(lists.SOURCE_COUNTS.values())
    index.write_text(index.read_text()+'corrupt\n')
    with pytest.raises(ValueError,match='CSV checksum mismatch'):
        lists.load_converted(directory,registry)
    with pytest.raises(FileExistsError):
        converter.convert(tmp_path,directory,registry)


def test_supplementary_membership_absence_is_unknown_and_nearby_stars_are_not_clusters(monkeypatch):
    from astropy.table import Table
    _union_tool_and_sources(monkeypatch)
    import observing_list_membership as lists
    table=Table(dict(wenu_id=['W1'],dias_id=['NGC 457'],hunt_name=['NGC_457'],
                     Other_ids=['NGC 457'],Messier_id=[''],Caldwell_id=['']))
    record=dict(catalogue='sac_red_stars',designation='HD 11224',
                identifiers=['HD 11224'],source_file='synthetic.csv')
    _,summary=lists.annotate(table,[record])
    assert not table['in_sac_red_stars'][0]
    assert np.ma.is_masked(table['in_sac_urban'][0])
    assert summary['counts']['sac_urban']['unresolved_rows']==1
    assert len(table)==1 and table['dias_id'][0]=='NGC 457'
    table['Messier_id']=['M 45']
    lists.annotate(table,[dict(catalogue='sac_urban',designation='M 45',identifiers=['M 45'],source_file='synthetic.csv')])
    assert table['in_sac_urban'][0]


def test_first_list_plot_preserves_source_radii_shared_v10_masks_and_strict_cut(monkeypatch,capsys):
    from astropy.table import Table,MaskedColumn
    import pytest
    _union_tool_and_sources(monkeypatch)
    import plot_merged_open_clusters as plot
    table=Table(dict(wenu_id=['W1','W2'],dias_id=['NGC 457','Dias only'],
      dias_apparent_diameter_arcmin=[20.,30.],hunt_apparent_diameter_arcmin=[10.,np.nan],
      in_messier=[True,False],in_caldwell=[True,True]))
    table['in_sac_urban']=MaskedColumn([True,True],mask=[False,True])
    table['hunt_id']=MaskedColumn([1,0],mask=[False,True])
    table['hunt_v10']=MaskedColumn([11.,0.],mask=[False,True])
    assert list(plot.first_membership(table,['messier','caldwell','sac_urban']))==['messier','caldwell']
    data=plot.points(table,['messier','caldwell'])
    assert list(data['radius_arcmin'])==[10.,5.,15.]
    assert list(data['selection_status'])==['plotted','plotted','missing_v10']
    assert list(data['v10'][:2])==[11.,11.]
    cut=plot.points(table,['messier','caldwell'],max_v10=11)
    assert list(cut['selection_status'])==['v10_cut','v10_cut','missing_v10']
    with pytest.raises(ValueError,match='distinct'):
        plot.first_membership(table,['messier','messier'])
    assert plot.main([])==0
    assert '--priority' in capsys.readouterr().out


def test_supplementary_conversion_requires_complete_csvs_and_detects_corruption(tmp_path,monkeypatch):
    import csv,hashlib,json,pytest
    _union_tool_and_sources(monkeypatch)
    import observing_list_additions as additions
    monkeypatch.setattr(additions,'COUNTS',{'sac_urban':1})
    registry=tmp_path/'registry.json'
    registry.write_text(json.dumps(dict(products=[dict(file='source.html',sha256='0'*64)])))
    directory=tmp_path/'csv';directory.mkdir()
    index=directory/'observing_memberships_v1.csv'
    with index.open('w',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['catalogue','designation','identifiers_json','source_file'])
        writer.writerow(['sac_urban','NGC 457',json.dumps(['NGC 457']),'source.html'])
    source=directory/'sac_urban_list_v1.csv';source.write_text('identifier\nNGC 457\n')
    receipt=dict(source_registry_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
      source_sha256={'source.html':'0'*64},products=[dict(file=p.name,bytes=p.stat().st_size,
      sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [index,source]])
    path=directory/'conversion_receipt_v1.json';path.write_text(json.dumps(receipt))
    records,_=additions.load_converted(directory,registry)
    assert records[0]['identifiers']==['NGC 457']
    source.write_text('corrupted\n')
    with pytest.raises(ValueError,match='checksum'):
        additions.load_converted(directory,registry)
    receipt['products']=receipt['products'][:1];path.write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='Incomplete'):
        additions.load_converted(directory,registry)


def test_member_count_axis_uses_each_source_count_without_halving_or_radius_dependency(monkeypatch):
    from astropy.table import Table,MaskedColumn
    _union_tool_and_sources(monkeypatch)
    import plot_merged_open_clusters as plot
    table=Table(dict(wenu_id=['W1','W2','W3'],dias_id=['A','B','C'],hunt_id=[1,2,3],
      hunt_v10=[10.,11.,12.],dias_member_count=[31,0,-1],hunt_member_count=[120,80,50],
      hunt_accepted_member_count=[40,30,20],in_messier=[True,False,False]))
    # No radius columns: members mode must not require or substitute radii.
    table['dias_member_count']=MaskedColumn(table['dias_member_count'],mask=[False,False,True])
    data=plot.points(table,['messier'],x='members',max_v10=11)
    assert list(data['x_value'][:2])==[31.,120.]
    assert list(data['selection_status'])==['plotted','plotted','invalid_members','v10_cut','invalid_members','v10_cut']
    assert np.all(np.isnan(data['radius_arcmin']))
    assert list(data['first_list'][:2])==['messier','messier']
    assert list(data['v10'][:2])==[10.,10.]


def test_member_count_cli_exports_axis_metadata_and_no_argument_help(tmp_path,monkeypatch,capsys):
    import json
    from astropy.table import Table
    _union_tool_and_sources(monkeypatch)
    import plot_merged_open_clusters as plot
    table=Table(dict(wenu_id=['W1'],dias_id=['A'],hunt_id=[1],hunt_v10=[10.],
                     dias_member_count=[31],hunt_member_count=[120],in_messier=[True]))
    path=tmp_path/'candidate_v1.ecsv';table.write(path)
    output=tmp_path/'plots'
    assert plot.main(['--catalogue',str(path),'--output-directory',str(output),
                      '--name','members_v10_v1','--x','members'])==0
    receipt=json.loads((output/'members_v10_v1_summary.json').read_text())
    assert receipt['x']=='members'
    assert receipt['x_columns']==['dias_member_count','hunt_member_count']
    ledger=Table.read(output/'members_v10_v1_points.csv')
    assert list(ledger['x_value'])==[31.,120.]
    assert all((output/('members_v10_v1'+extension)).exists() for extension in ('.png','.svg','.pdf'))
    capsys.readouterr()
    assert plot.main([])==0
    help_text=capsys.readouterr().out
    assert '--x {radius,members}' in help_text and 'member_count' in help_text


def test_v01_selection_mandatory_override_and_strict_log_radius_boundaries(monkeypatch):
    from astropy.table import Table,MaskedColumn
    _union_tool_and_sources(monkeypatch)
    import curate_open_clusters as curator
    table=Table(dict(wenu_id=['W1','W2','W3','W4','W5','W6'],has_dias=[False]*5+[True],has_hunt=[True]*6,
      hunt_v10=[12.499,5.,4.999,np.nan,10.,10.],hunt_apparent_diameter_arcmin=[2.,2000.,2000.,2.,2.,2.],
      hunt_member_count=[20]*6,hunt_reddening_e_bv=[3.,3.,3.,np.nan,3.01,1.],
      dias_apparent_diameter_arcmin=[np.nan]*5+[2000.],dias_member_count=[0]*5+[50],dias_reddening_e_bv=[np.nan]*5+[1.]))
    for name in curator.MANDATORY: table['in_'+name]=MaskedColumn([False]*6,mask=False)
    table['in_messier'][3]=True
    selected=curator.selection(table)
    assert list(selected['selection_selected'])==[True,False,True,True,False,False]
    assert selected['selection_hunt_v10_boundary'][0]==17.5
    assert selected['selection_hunt_v10_boundary'][1]==5.
    assert selected['selection_retained_by_mandatory_list'][3]
    assert selected['selection_hunt_numeric_reason'][4]=='ebv_cut'
    assert not selected['selection_retained_by_numeric_intersection'][5]
    assert curator.selection(table,source_policy='any')['selection_retained_by_numeric_intersection'][5]
    table['hunt_v10'][0]=12.5
    table['in_sac_urban'].mask[4]=True
    selected=curator.selection(table)
    assert not selected['selection_selected'][0]
    assert selected['selection_retained_by_mandatory_review'][4]


def test_v01_positional_pairing_preserves_source_values_and_id_lineage(monkeypatch):
    from astropy.table import Table
    tool,_,_,caldwell,messier=_union_tool_and_sources(monkeypatch)
    import curate_open_clusters as curator
    dias=Table(dict(identifier=['Dias A'],ra_deg=[1.],dec_deg=[0.],apparent_diameter_arcmin=[30.],member_count=[31]))
    hunt=Table(dict(identifier=['Hunt B'],hunt_id=[7],aliases=[''],ra_deg=[1.01],dec_deg=[0.],
                    apparent_diameter_arcmin=[10.],member_count=[120],v10=[10.]))
    union,*_=tool.merge_catalogues(dias,hunt,caldwell,messier)
    original_ids=set(union['wenu_id'])
    output,ledger,summary=curator.position_pairs(union)
    assert len(union)==2 and len(output)==1
    assert summary['added_positional_pairs']==1
    assert set(output['previous_wenu_ids'][0].split('|'))==original_ids
    assert output['dias_member_count'][0]==31 and output['hunt_member_count'][0]==120
    assert output['dias_ra_deg'][0]==1. and output['hunt_ra_deg'][0]==1.01
    assert output['RA'][0]==1.01 and output['has_dias'][0] and output['has_hunt'][0]
    assert output['positional_pair_provisional'][0]
    assert ledger['curation_pair_decision'][0]=='paired_position_provisionally'
    audit,_,_=curator.position_pairs(union,'audit-only')
    assert len(audit)==2
    # Two Hunt candidates for one Dias row remain separate, regardless of order.
    hunt.add_row(dict(identifier='Hunt C',hunt_id=8,aliases='',ra_deg=1.02,dec_deg=0.,
                      apparent_diameter_arcmin=10.,member_count=80,v10=9.))
    union,*_=tool.merge_catalogues(dias,hunt,caldwell,messier)
    output,ledger,summary=curator.position_pairs(union)
    assert len(output)==3 and summary['added_positional_pairs']==0
    assert set(ledger['curation_pair_decision'])=={'competing_position_candidates'}
    hunt=hunt[:1]
    union,*_=tool.merge_catalogues(dias,hunt,caldwell,messier)
    union['identity_review'][0]=True
    output,ledger,summary=curator.position_pairs(union)
    assert len(output)==1 and summary['added_positional_pairs']==1
    assert output['identity_review'][0] and output['positional_pair_provisional'][0]


def test_v01_curator_help_and_unverified_mandatory_lists_fail_before_writing(tmp_path,monkeypatch,capsys):
    from astropy.table import Table
    import pytest
    _union_tool_and_sources(monkeypatch)
    import curate_open_clusters as curator
    assert curator.main([])==0
    assert '--source-policy' in capsys.readouterr().out
    table=Table(dict(wenu_id=['W1']))
    source=tmp_path/'source_v1.ecsv';table.write(source)
    destination=tmp_path/'output'
    with pytest.raises(ValueError,match='Mandatory list unavailable'):
        curator.main(['--catalogue',str(source),'--output-directory',str(destination)])
    assert not destination.exists()


def test_depurated_catalogue_preserves_sources_masks_and_active_selector(tmp_path, monkeypatch):
    """The new seam excludes only the agreed types/absences and freezes IDs."""
    import sys
    from pathlib import Path
    import pytest
    from astropy.table import Table, MaskedColumn
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'tools'))
    import prepare_open_cluster_catalogue as preparation
    table = Table(dict(wenu_id=['W1','W2','W3','W4','W5','W6'], RA=[0.]*6,Dec=[0.]*6,
        has_dias=[True,False,False,False,False,False],has_hunt=[True]*6,
        dias_id=['NGC 1','','','','',''],hunt_name=['NGC_1','HSC_2','HSC_3','HSC_4','OC_5','HSC_6'],
        hunt_type=['o','o','g','m','o','o'],Other_ids=['','','','','',''],identity_review=[False]*6))
    table['in_messier'] = MaskedColumn([False]*6,mask=[False,False,False,False,False,True])
    for source in ('dias','hunt'):
        for column in ('ra_deg','dec_deg','apparent_diameter_arcmin','distance_pc','reddening_e_bv','member_count'):
            table[source+'_'+column]=[2.]*6
    table['dias_source_type_flag']=MaskedColumn(['',0,0,0,0,0],dtype=object,mask=[False,True,True,True,True,True])
    table['hunt_v10']=[9.]*6
    original = table.copy()
    selected, marked = preparation.depurate(table)
    assert list(selected['wenu_id'])==['W1','W5','W6']  # OC is external; unknown claims retained.
    assert list(marked['depuration_reason'])==['','single_source_no_other_compilation','hunt_type_g','hunt_type_m','','']
    assert table.colnames==original.colnames
    from wenu.sky.native_snapshot import _table_records, _table_from_records
    restored=_table_from_records(_table_records(selected))
    assert restored['dias_source_type_flag'].mask.tolist()==[False,True,True]
    assert np.asarray(restored['dias_source_type_flag'],dtype=object).tolist()==['',None,None]
    assert 'magnitude' not in selected.colnames and 'v_magnitude' not in selected.colnames
    assert selected['hunt_v10'].tolist()==[9.]*3
    selected.meta.update(selection_policy=dict(mandatory_lists=['messier'],
        mandatory_policy='Mandatory rows bypass numeric cuts.', numeric_policy='Positive counts and radii.',
        boundary='V10 < 17.5-(12.5/3)*log10(radius_arcmin)', max_v10=12.5,
        max_ebv=3.,source_policy='all',position_policy='Provisional pairs retain source positions.'),
        depuration=dict(input_sha256='synthetic-parent'))
    path=tmp_path/'wenu_open_clusters_v0.2.ecsv';selected.write(path)
    selector=preparation.install(path,tmp_path/'installed',activate=True)
    assert selector.is_symlink() and selector.readlink()==Path(path.name)
    assert selector.read_bytes()==path.read_bytes()
    layer=OpenClusters(None);layer.load(filename=selector)
    geometry=layer.position()
    assert list(geometry.ids)==['W1','W5','W6'] and list(geometry.labels)==['NGC 1','OC 5','HSC 6']
    assert len(layer._selected_table(['W5']))==1
    assert np.ma.is_masked(layer.catalog['in_messier'][2])
    with pytest.raises(FileExistsError): preparation.install(path,tmp_path/'installed',activate=True)
    # A regular selector file is never overwritten, including on a new version.
    other=tmp_path/'regular';other.mkdir();(other/'open_star_clusters.ecsv').write_text('keep')
    with pytest.raises(ValueError): preparation.install(path,other,activate=True)
    assert not (other/path.name).exists()
    positions=preparation.positional_review(selected)
    assert len(set(zip(positions['wenu_id_a'],positions['wenu_id_b'])))==3
    assert preparation.main([])==0
    invalid=selected.copy();invalid['hunt_type'][0]='g'
    with pytest.raises(ValueError): OpenClusters.normalize_catalogue(invalid)
    import hashlib,json
    evidence=path.with_name(path.stem+'_positions.csv');evidence.write_text('review\n')
    summary=path.with_name(path.stem+'_summary.json')
    summary.write_text(json.dumps(dict(input_sha256='synthetic-parent', excluded_counts={'hunt_type_g':1},
        products={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [path,evidence]})))
    accepted=tmp_path/'curated'
    selector=preparation.promote_catalogue(path,accepted,activate=True)
    assert selector.is_symlink() and (accepted/evidence.name).read_bytes()==evidence.read_bytes()
    assert path.is_file() and summary.is_file()  # output trials remain
    preparation.promote_catalogue(path,accepted,activate=True)  # same immutable bytes reused
    evidence.write_text('tampered')
    with pytest.raises(ValueError,match='checksum'): preparation.promote_catalogue(path,tmp_path/'bad')
    assert not (tmp_path/'bad').exists()
    import plot_merged_open_clusters as plot
    before = selector.read_bytes()
    assert plot.main(['--catalogue',str(selector),'--criteria-pages']) == 0
    criteria_path = accepted/'wenu_open_clusters_v0.2_criteria_v1.json'
    criteria = json.loads(criteria_path.read_text())
    assert criteria['catalogue']['sha256'] == hashlib.sha256(before).hexdigest()
    assert len(criteria['pages']) == 3
    assert all('_v0.2_criteria_v1_' in p['file'] for p in criteria['pages'])
    assert selector.read_bytes() == before
    with pytest.raises(FileExistsError): plot.publish_criteria(selector)


def test_working_data_migration_keeps_receipts_and_list_memberships(tmp_path,monkeypatch):
    import csv,hashlib,json
    from pathlib import Path
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]/'tools'))
    import observing_list_membership as original
    import observing_list_additions as additions
    from migrate_catalogue_data import migrate
    from catalogue_data_layout import data_file
    monkeypatch.setattr(original,'SOURCE_FILES',['messier_list_v1.csv'])
    monkeypatch.setattr(original,'LISTS',['messier'])
    monkeypatch.setattr(original,'SOURCE_COUNTS',{'messier':1})
    monkeypatch.setattr(additions,'COUNTS',{'sac_urban':1})
    legacy=tmp_path/'legacy';destination=tmp_path/'data/observing_lists';destination.mkdir(parents=True)
    source_bytes={}
    for batch,source_folder,csv_folder,registry_name,list_id,source_file,csv_file in [
        ('original','sources_v1','csv_v1','observing_sources_v1.json','messier','messier_list_v1.csv','messier_list_v1.csv'),
        ('additions','sources_additions_v1','csv_additions_v1','observing_additions_v1.json','sac_urban','sac_urban_source_v1.html','sac_urban_list_v1.csv')]:
        source=legacy/source_folder;converted=legacy/csv_folder;source.mkdir(parents=True);converted.mkdir()
        raw=b'object\nM 1\n';(source/source_file).write_bytes(raw)
        registry=destination/registry_name
        registry.write_text(json.dumps({'products':[dict(file=source_file,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())]}))
        (converted/csv_file).write_bytes(raw)
        index=converted/'observing_memberships_v1.csv'
        with index.open('w',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['catalogue','designation','identifiers_json','source_file'])
            writer.writerow([list_id,'M 1','["M 1"]',source_file])
        receipt=dict(source_registry_sha256=hashlib.sha256(registry.read_bytes()).hexdigest(),
            source_sha256={source_file:hashlib.sha256(raw).hexdigest()},products=[dict(file=p.name,bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [converted/csv_file,index]])
        r=converted/'conversion_receipt_v1.json';r.write_text(json.dumps(receipt));source_bytes[batch]=r.read_bytes()
    report=migrate(legacy,destination)
    assert not legacy.exists() and report['migrated_files']==8
    assert (destination/'messier/provenance_original_v1.json').is_file()
    assert (destination/'sac_urban/provenance_additions_v1.json').is_file()
    for batch in source_bytes:
        assert data_file(destination,'conversion_receipt_v1.json',batch).read_bytes()==source_bytes[batch]
    assert len(original.load_converted(destination,destination/'observing_sources_v1.json')[0])==1
    assert len(additions.load_converted(destination,destination/'observing_additions_v1.json')[0])==1
    # Conflicts fail before source removal/copy.
    from catalogue_data_layout import copy_verified
    source=tmp_path/'new';source.write_bytes(b'new')
    target=tmp_path/'old';target.write_bytes(b'old')
    import pytest
    with pytest.raises(FileExistsError): copy_verified([(source,target)])
    assert source.read_bytes()==b'new' and target.read_bytes()==b'old'

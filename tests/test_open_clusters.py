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
    path = nonstellar_catalog_path("open_clusters")
    assert path.is_file()
    layer = OpenClusters(observer())
    table = layer.load()
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
    dias = Table.read(nonstellar_catalog_path('open_clusters'))
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
    layer.load()
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
    layer.load()

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
        source = Path(nonstellar_catalog_path(category))
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
    dias.meta['coordinate_frame'] = 'ICRS/J2000 as supplied'
    hunt = Table(dict(identifier=['NGC_869','NGC_884','Melotte_22'],hunt_id=[1,2,3],
        aliases=['NGC_869,Shared alias','NGC_884,Shared alias','Melotte_22'],
        ra_deg=[1.1,2.1,5.],dec_deg=[10.1,20.1,50.],hunt_type=['g','m','o'],
        v5=[9.,10.,np.nan]))
    hunt.meta['coordinate_epoch'] = 'J2016.0'
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
    extended.add_row(dict(identifier='AAA new',ra_deg=0.,dec_deg=0.,member_count=1,source_type_flag=''))
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
        '--name','wenu_open_clusters_v1']
    assert tool.main(arguments)==0
    catalogue = Table.read(output/'wenu_open_clusters_v1.ecsv')
    assert len(catalogue)==5 and catalogue.meta['curation_status']=='unreviewed_candidate'
    assert catalogue.meta['source_sha256']['dias']==hashlib.sha256((data/'open_clusters/dias.ecsv').read_bytes()).hexdigest()
    for name in ['_crosswalk.csv','_references.csv','_ids.json','_summary.json']:
        assert (output/('wenu_open_clusters_v1'+name)).exists()
    receipt = json.loads((output/'wenu_open_clusters_v1_summary.json').read_text())
    assert receipt['dias_rows']==4 and receipt['hunt_rows']==3
    assert all(hashlib.sha256((output/name).read_bytes()).hexdigest()==value for name,value in receipt['products'].items())
    with pytest.raises(FileExistsError):
        tool.main(arguments)
    with pytest.raises(SystemExit):
        tool.main(['--name','unversioned'])

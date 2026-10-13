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

"""Current isophotes contracts."""

# Contracts consolidated from test_milestone33_milky_way_isophotes.py.
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
import astropy.units as u
from matplotlib.path import Path
from astropy.time import Time

from wenu.coordinates import GENERIC_SPHERICAL_SPEC

from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import ProjectedPolygon, ProjectedPolygons
from wenu.rendering import layers
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.resources import milky_way_isophote_path
from wenu.sky.milky_way import MilkyWayIsophotes
from wenu.projections.stereographic import StereographicProjection
from wenu.rendering.preparation import project_polygons_to_projection_cap


class Observer:
    altaz_frame = AltAz(
        obstime=Time("2026-08-15 21:00"),
        location=EarthLocation.from_geodetic(-71.23, -32.45),
    )


@pytest.mark.parametrize("level", ["ol1", "ol2"])
def test_native_icrs_isophotes_keep_source_rings_topology_and_cache(level, monkeypatch):
    from wenu.sky.realization import NATIVE_ICRS_SPEC
    from wenu.sky.realization import LayerRealizationContext
    from wenu.sky.milky_way import _native_ring_interior
    layer = MilkyWayIsophotes(Observer(), levels=(level,)).load()
    def forbidden(*args, **kwargs):
        raise AssertionError("Native isophotes requested observer transformation")
    monkeypatch.setattr(layer, "_transform_rings", forbidden)
    geometry = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
    assert geometry.coordinate_spec.frame == "icrs"
    assert geometry.metadata["coordinate_system"] == "icrs"
    index = 0
    for polygon in layer.features[level]:
        for ring_index, ring in enumerate(polygon):
            ring = np.array(ring, dtype=float)
            if np.allclose(ring[0, :2], ring[-1, :2]):
                ring = ring[:-1]
            np.testing.assert_array_equal(geometry.lon_deg[index], ring[:, 0])
            np.testing.assert_array_equal(geometry.lat_deg[index], ring[:, 1])
            assert geometry.metadata["is_hole"][index] == (ring_index > 0)
            winding = geometry.metadata["projection_cap_topology_inversion"][index]
            left, area = _native_ring_interior(ring[:, :2], winding)
            assert geometry.metadata["spherical_interior_left"][index] == left
            assert geometry.metadata["spherical_interior_area_sr"][index] == pytest.approx(area)
            index += 1
    assert index == len(geometry)
    assert not layer._observed_polygon_cache


def test_native_polar_ol1_raster_matches_independent_source_membership():
    from wenu.sky.realization import LayerRealizationContext, NATIVE_ICRS_SPEC
    layer = MilkyWayIsophotes(None, levels=("ol1",)).load()
    projection = StereographicProjection()
    ra,dec = np.meshgrid(np.arange(0,360,7.3), np.arange(5,80,6.7))
    x,y = projection.project_spherical(ra.ravel(), dec.ravel())
    samples = np.column_stack((x,y))
    expected = np.zeros(len(samples), dtype=bool)
    for polygon in layer.features["ol1"]:
        inside = np.ones(len(samples), dtype=bool)
        for index,ring in enumerate(polygon):
            ring = np.array(ring)
            px,py = projection.project_spherical(ring[:,0], ring[:,1])
            contained = Path(np.column_stack((px,py))).contains_points(samples)
            if index < 2:
                contained = ~contained
            inside &= contained if index == 0 else ~contained
        expected |= inside
    geometry = layer.realize(LayerRealizationContext(NATIVE_ICRS_SPEC), None)
    projected = project_polygons_to_projection_cap(geometry, projection=projection, angular_radius_deg=100)
    figure,ax = plt.subplots(figsize=(8,8), dpi=100, facecolor="black")
    try:
        ax.set_facecolor("black")
        ax.set(xlim=(-2.4,2.4), ylim=(-2.4,2.4), aspect="equal")
        ax.set_axis_off()
        MatplotlibRenderer(ax).draw(projected, compound_by="compound_id",
            polygon_fill_style={"facecolor":"white", "face_alpha":1})
        figure.canvas.draw()
        pixels = np.asarray(figure.canvas.buffer_rgba())[:,:,0]
        tested = 0
        for i,(col,row) in enumerate(ax.transData.transform(samples).astype(int)):
            row = len(pixels)-1-row
            window = pixels[row-2:row+3,col-2:col+3]
            if window.size == 25 and (np.all(window < 5) or np.all(window > 250)):
                assert bool(pixels[row,col] > 128) == expected[i]
                tested += 1
        assert tested > 350
    finally:
        plt.close(figure)


@pytest.mark.parametrize("hour", [0, 4, 6, 9, 12, 15, 18, 21])
def test_ol1_rendered_fill_matches_native_sky_across_a_day(hour):
    """Compare actual raster fill with native catalogue membership.

    UTC 04:00 is the reported La Ligua 01:00 local inversion. The remaining
    orientations also exercise fully visible rings and extra cap windings.
    """
    observer = Observer()
    observer.altaz_frame = AltAz(
        obstime=Time(f"2026-10-16T{hour:02d}:00:00"),
        location=EarthLocation.from_geodetic(-71.230289, -32.443342, 52),
    )
    layer = MilkyWayIsophotes(observer, levels=("ol1",)).load()
    projection = StereographicProjection()
    ra, dec = np.meshgrid(np.arange(0, 360, 7.3), np.arange(-75, 80, 6.7))
    ra, dec = ra.ravel(), dec.ravel()
    x, y = projection.project_spherical(ra, dec)
    native_samples = np.column_stack((x, y))
    expected = np.zeros(len(ra), dtype=bool)
    for polygon in layer.features["ol1"]:
        inside = np.ones(len(ra), dtype=bool)
        for index, ring in enumerate(polygon):
            ring = np.asarray(ring)
            x, y = projection.project_spherical(ring[:, 0], ring[:, 1])
            contained = Path(np.column_stack((x, y))).contains_points(native_samples)
            # The two principal OL1 rings enclose the unbounded side of
            # their native north-pole outlines; small holes are bounded.
            if index < 2:
                contained = ~contained
            inside &= contained if index == 0 else ~contained
        expected |= inside
    observed = SkyCoord(ra=ra * u.deg, dec=dec * u.deg).transform_to(
        observer.altaz_frame
    )
    x, y = projection.project_spherical(observed.az.deg, observed.alt.deg)
    projected = project_polygons_to_projection_cap(
        layer.spherical_geometry(observer),
        projection=projection,
        angular_radius_deg=89.999,
    )
    figure = plt.figure(figsize=(10, 10), dpi=100, facecolor="black")
    ax = figure.add_axes([0, 0, 1, 1], facecolor="black")
    ax.set(xlim=(-2, 2), ylim=(-2, 2))
    ax.set_axis_off()
    MatplotlibRenderer(ax).draw(
        projected, compound_by="compound_id",
        polygon_fill_style={"facecolor": "white", "face_alpha": 1},
    )
    figure.canvas.draw()
    pixels = np.asarray(figure.canvas.buffer_rgba())[:, :, 0]
    sample_pixels = ax.transData.transform(np.column_stack((x, y)))
    tested = 0
    for index in np.flatnonzero(observed.alt.deg > 2):
        col, row = np.floor(sample_pixels[index]).astype(int)
        row = len(pixels) - 1 - row
        window = pixels[row - 2:row + 3, col - 2:col + 3]
        # Exclude only raster-edge samples; test both bright and dark sky.
        if window.size != 25 or np.max(window) != np.min(window):
            continue
        assert bool(pixels[row, col] > 127) == bool(expected[index]), (
            hour, ra[index], dec[index]
        )
        tested += 1
    plt.close(figure)
    assert tested > 450


def _catalogue(path):
    features = []
    for index, level in enumerate(MilkyWayIsophotes.available_levels):
        outer = [
            [index, -2], [index + 3, -2],
            [index + 3, 2], [index, 2], [index, -2],
        ]
        rings = [outer]
        if level == "ol1":
            rings.append([
                [index + 1, -1], [index + 1, 1],
                [index + 2, 1], [index + 2, -1],
                [index + 1, -1],
            ])
        features.append({
            "type": "Feature",
            "id": level,
            "properties": {},
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [[*rings]],
            },
        })
    path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": features,
    }))
    return path


def test_layer_preserves_compound_ring_topology(tmp_path):
    layer = MilkyWayIsophotes(
        Observer(),
        levels=MilkyWayIsophotes.available_levels,
    )
    layer.load(_catalogue(tmp_path / "mw.json"))
    geometry = layer.spherical_geometry(Observer())
    assert len(geometry) == 6
    assert geometry.metadata["level"].tolist()[:2] == ["ol1", "ol1"]
    assert geometry.metadata["compound_id"].tolist()[:2] == [
        "ol1:0", "ol1:0"
    ]
    assert geometry.metadata["is_hole"].tolist()[:2] == [False, True]
    assert geometry.metadata[
        "projection_cap_topology_inversion"
    ].tolist()[:2] == [False, False]
    assert geometry.metadata["semantic_entity_keys"].tolist()[:2] == [
        "isophote_ol1", "isophote_ol1"
    ]
    assert geometry.metadata[
        "semantic_entity_display_names"
    ].tolist()[:2] == ["Isophote OL1", "Isophote OL1"]
    assert all(np.all(np.isfinite(values)) for values in geometry.lon_deg)


def test_level_selection_is_ordered_and_valid(tmp_path):
    layer = MilkyWayIsophotes(
        Observer(),
        levels=("ol4", "ol2"),
    )
    layer.load(_catalogue(tmp_path / "mw.json"))
    geometry = layer.spherical_geometry(Observer())
    assert geometry.metadata["level"].tolist() == ["ol2", "ol4"]
    with pytest.raises(ValueError, match="Unknown"):
        MilkyWayIsophotes(Observer(), levels=("ol6",))


def test_level_selection_can_change_per_render_without_mutation(tmp_path):
    layer = MilkyWayIsophotes(
        Observer(), levels=MilkyWayIsophotes.available_levels
    )
    layer.load(_catalogue(tmp_path / "mw.json"))

    selected = layer.spherical_geometry(
        Observer(), levels={"ol4", "ol2"}
    )
    complete = layer.spherical_geometry(Observer())

    assert selected.metadata["level"].tolist() == ["ol2", "ol4"]
    assert set(complete.metadata["level"]) == set(layer.available_levels)
    assert layer.levels == layer.available_levels


def test_renderer_groups_rings_into_one_compound_patch():
    polygons = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[0, 4, 4, 0],
                y=[0, 0, 4, 4],
            ),
            ProjectedPolygon(
                x=[1, 1, 3, 3],
                y=[1, 3, 3, 1],
            ),
        ],
        metadata={
            "compound_id": np.asarray(["level", "level"], dtype=object),
            "semantic_entity_keys": np.asarray(
                ["isophote_ol2", "isophote_ol2"], dtype=object
            ),
            "semantic_entity_display_names": np.asarray(
                ["Isophote OL2", "Isophote OL2"], dtype=object
            ),
        },
    )
    figure, ax = plt.subplots()
    artists = MatplotlibRenderer(ax).draw(
        polygons,
        compound_by="compound_id",
        polygon_fill_style={
            "facecolor": "white",
            "face_alpha": 0.2,
            "zorder": layers.MILKY_WAY,
        },
        polygon_marker_style={"color": "white"},
    )
    assert len(artists) == 3
    assert len(artists[0].get_path().codes) == 10
    assert artists[0].get_zorder() == layers.MILKY_WAY
    assert all(
        artist._wenu_semantic_entity_key == "isophote_ol2"
        for artist in artists
    )
    assert all(
        artist._wenu_semantic_entity_display_name == "Isophote OL2"
        for artist in artists
    )
    plt.close(figure)


def test_publication_style_uses_named_milky_way_zorder(tmp_path):
    layer = MilkyWayIsophotes(Observer())
    layer.load(_catalogue(tmp_path / "mw.json"))
    sky = type("Sky", (), {
        "stars": None,
        "nonstellar": None,
        "galaxies": None,
        "globular_clusters": None,
        "milky_way_isophotes": layer,
        "constellation_lines": None,
        "constellation_labels": None,
        "constellation_boundaries": None,
        "points": None,
        "layers": (layer,),
    })()
    render = PublicationStyle().layer_options(sky)[layer]["render"]
    assert render["compound_by"] == "compound_id"
    assert (
        render["polygon_fill_style"]["zorder"]
        == layers.MILKY_WAY
    )


def test_packaged_snapshot_has_expected_levels():
    layer = MilkyWayIsophotes(Observer()).load()
    assert tuple(layer.features) == layer.available_levels
    assert set(layer.sources) == set(layer.available_levels)
    for level in layer.available_levels:
        path = milky_way_isophote_path(level)
        document = json.loads(path.read_text(encoding="utf-8"))
        assert [feature["id"] for feature in document["features"]] == [level]
        assert layer.sources[level] == str(path)


def test_packaged_ol1_records_its_two_source_pole_windings():
    geometry = MilkyWayIsophotes(Observer()).load().spherical_geometry(
        Observer(), levels={"ol1"}
    )

    inversions = geometry.metadata[
        "projection_cap_topology_inversion"
    ]
    assert inversions[:2].tolist() == [True, True]
    assert not np.any(inversions[2:])


def test_explicit_level_geometry_names_only_its_single_level_file():
    layer = MilkyWayIsophotes(
        Observer(), levels=MilkyWayIsophotes.available_levels
    ).load()

    geometry = layer.spherical_geometry(Observer(), levels={"ol3"})

    assert set(geometry.metadata["level"]) == {"ol3"}
    assert set(geometry.metadata["source"]) == {
        str(milky_way_isophote_path("ol3"))
    }


def test_style_clips_isophotes_before_planar_rendering(tmp_path):
    """Below-horizon complements must not tint the visible sky."""
    from wenu.geometry.spherical import SphericalPolygons

    layer = MilkyWayIsophotes(Observer())
    layer.load(_catalogue(tmp_path / "mw.json"))
    sky = type("Sky", (), {
        "stars": None,
        "nonstellar": None,
        "galaxies": None,
        "globular_clusters": None,
        "milky_way_isophotes": layer,
        "constellation_lines": None,
        "constellation_labels": None,
        "constellation_boundaries": None,
        "points": None,
        "layers": (layer,),
    })()
    prepare = PublicationStyle().layer_options(sky)[layer]["prepare"]

    spherical = SphericalPolygons(coordinate_spec=GENERIC_SPHERICAL_SPEC,
        lon_deg=(
            np.asarray([0.0, 1.0, 1.0, 0.0]),
            np.asarray([2.0, 3.0, 3.0, 2.0]),
        ),
        lat_deg=(
            np.asarray([-4.0, -4.0, -1.0, -1.0]),
            np.asarray([-1.0, 1.0, 2.0, -1.0]),
        ),
        metadata={
            "compound_id": np.asarray(["outside", "crossing"]),
            "is_hole": np.asarray([False, False]),
        },
    )
    projected = ProjectedPolygons(
        items=[
            ProjectedPolygon(
                x=[0.0, 1.0, 1.0, 0.0],
                y=[0.0, 0.0, 1.0, 1.0],
            ),
            ProjectedPolygon(
                x=[2.0, 3.0, 3.0, 2.0],
                y=[0.0, 0.0, 1.0, 1.0],
            ),
        ],
        metadata=dict(spherical.metadata),
    )

    clipped = prepare(spherical, projected)
    assert len(clipped) == 1
    assert clipped.metadata["compound_id"].tolist() == ["crossing"]
    assert np.all(np.isfinite(clipped[0].x))
    assert np.all(np.isfinite(clipped[0].y))

def test_default_levels_start_at_ol2(tmp_path):
    layer = MilkyWayIsophotes(Observer())
    assert layer.levels == ("ol2", "ol3", "ol4", "ol5")

    layer.load(_catalogue(tmp_path / "mw.json"))
    geometry = layer.spherical_geometry(Observer())
    assert "ol1" not in geometry.metadata["level"]
    assert set(geometry.metadata["level"]) == {
        "ol2", "ol3", "ol4", "ol5"
    }


def test_outer_level_remains_explicitly_available(tmp_path):
    layer = MilkyWayIsophotes(
        Observer(),
        levels=("ol1",),
    )
    layer.load(_catalogue(tmp_path / "mw.json"))
    geometry = layer.spherical_geometry(Observer())
    assert set(geometry.metadata["level"]) == {"ol1"}


def test_level_selections_transform_and_cache_only_requested_files(
    tmp_path, monkeypatch
):
    layer = MilkyWayIsophotes(Observer()).load(
        _catalogue(tmp_path / "mw.json")
    )
    observer = Observer()
    original = layer._transform_rings
    calls = []

    def transform(rings, resolved):
        calls.append(len(rings))
        return original(rings, resolved)

    monkeypatch.setattr(layer, "_transform_rings", transform)
    selected = layer.spherical_geometry(observer, levels={"ol2"})
    complete = layer.spherical_geometry(
        observer, levels=layer.available_levels
    )
    selected_again = layer.spherical_geometry(observer, levels={"ol2"})

    assert set(selected.metadata["level"]) == {"ol2"}
    assert set(selected_again.metadata["level"]) == {"ol2"}
    assert set(complete.metadata["level"]) == set(layer.available_levels)
    assert calls == [len(selected), len(complete)]
    assert len(layer._observed_polygon_cache) == 2

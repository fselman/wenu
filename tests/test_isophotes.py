"""Current isophotes contracts."""

# Contracts consolidated from test_milestone33_milky_way_isophotes.py.
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from astropy.coordinates import AltAz, EarthLocation
from astropy.time import Time

from wenu.charts.styles import PublicationStyle
from wenu.geometry.projected import ProjectedPolygon, ProjectedPolygons
from wenu.rendering import layers
from wenu.rendering.matplotlib import MatplotlibRenderer
from wenu.sky.milky_way import MilkyWayIsophotes


class Observer:
    altaz_frame = AltAz(
        obstime=Time("2026-08-15 21:00"),
        location=EarthLocation.from_geodetic(-71.23, -32.45),
    )


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
    )
    assert len(artists) == 1
    assert len(artists[0].get_path().codes) == 10
    assert artists[0].get_zorder() == layers.MILKY_WAY
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

    spherical = SphericalPolygons(
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

def test_default_levels_exclude_outer_complement(tmp_path):
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
